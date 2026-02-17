import asyncpg
import secrets
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from .billing import get_pool

logger = logging.getLogger(__name__)


def _generate_slug(name: str) -> str:
    """Generate a slug from a name: lowercase, spaces to hyphens, remove special chars."""
    slug = name.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'[\s_-]+', '-', slug)  # Replace spaces/underscores with hyphens
    slug = slug.strip('-')  # Remove leading/trailing hyphens
    return slug


async def create_organization(name: str, owner_api_key_id: str) -> Dict[str, Any]:
    """
    Create a new organization with the given owner.
    
    Args:
        name: Organization name
        owner_api_key_id: API key ID of the owner
    
    Returns:
        Organization dict with id, name, slug, owner_api_key_id, tier, created_at
    """
    pool = await get_pool()
    org_id = secrets.token_hex(8)
    
    # Generate slug from name
    base_slug = _generate_slug(name)
    slug_suffix = secrets.token_hex(2)
    slug = f"{base_slug}-{slug_suffix}"
    
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Create organization
                org = await conn.fetchrow(
                    """INSERT INTO organizations (id, name, slug, owner_api_key_id, tier, max_members, created_at, updated_at)
                       VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                       RETURNING id, name, slug, owner_api_key_id, tier, max_members, settings, created_at, updated_at""",
                    org_id, name, slug, owner_api_key_id, "community", 10
                )
                
                # Add owner as member with 'owner' role
                await conn.execute(
                    """INSERT INTO org_members (org_id, api_key_id, role, joined_at)
                       VALUES ($1, $2, $3, NOW())""",
                    org_id, owner_api_key_id, "owner"
                )
                
                # Update api_keys to assign org_id
                await conn.execute(
                    "UPDATE api_keys SET org_id = $1 WHERE id = $2",
                    org_id, owner_api_key_id
                )
        
        logger.info(f"Created organization {org_id} with name '{name}' and owner {owner_api_key_id}")
        return dict(org) if org else {}
    
    except asyncpg.UniqueViolationError:
        logger.error(f"Slug '{slug}' already exists for organization")
        raise ValueError(f"Organization slug '{slug}' already exists")
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        raise


async def get_organization(org_id: str) -> Optional[Dict[str, Any]]:
    """
    Get organization with all its members.
    
    Args:
        org_id: Organization ID
    
    Returns:
        Organization dict with members list, or None if not found
    """
    pool = await get_pool()
    
    try:
        async with pool.acquire() as conn:
            # Get organization
            org = await conn.fetchrow(
                """SELECT id, name, slug, owner_api_key_id, tier, stripe_customer_id, 
                          max_members, settings, created_at, updated_at
                   FROM organizations WHERE id = $1""",
                org_id
            )
            
            if not org:
                return None
            
            # Get members
            members = await conn.fetch(
                """SELECT id, org_id, api_key_id, role, invited_by, joined_at
                   FROM org_members WHERE org_id = $1 ORDER BY joined_at""",
                org_id
            )
            
            org_dict = dict(org)
            org_dict["members"] = [dict(m) for m in members]
            
            return org_dict
    
    except Exception as e:
        logger.error(f"Error getting organization {org_id}: {e}")
        raise


async def list_organizations(api_key_id: str) -> List[Dict[str, Any]]:
    """
    List all organizations that the given API key belongs to.
    
    Args:
        api_key_id: API key ID
    
    Returns:
        List of organization dicts
    """
    pool = await get_pool()
    
    try:
        orgs = await pool.fetch(
            """SELECT DISTINCT o.id, o.name, o.slug, o.owner_api_key_id, o.tier, 
                      o.stripe_customer_id, o.max_members, o.settings, 
                      o.created_at, o.updated_at
               FROM organizations o
               INNER JOIN org_members om ON o.id = om.org_id
               WHERE om.api_key_id = $1
               ORDER BY o.created_at DESC""",
            api_key_id
        )
        
        return [dict(o) for o in orgs]
    
    except Exception as e:
        logger.error(f"Error listing organizations for {api_key_id}: {e}")
        raise


async def update_organization(org_id: str, name: Optional[str] = None, 
                            settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update organization fields.
    
    Args:
        org_id: Organization ID
        name: New name (optional)
        settings: New settings (optional)
    
    Returns:
        Updated organization dict
    """
    pool = await get_pool()
    
    try:
        # Build update query dynamically
        updates = ["updated_at = NOW()"]
        params = []
        param_count = 1
        
        if name is not None:
            updates.append(f"name = ${param_count}")
            params.append(name)
            param_count += 1
        
        if settings is not None:
            updates.append(f"settings = ${param_count}")
            params.append(settings)
            param_count += 1
        
        params.append(org_id)
        
        query = f"""UPDATE organizations 
                    SET {', '.join(updates)}
                    WHERE id = ${param_count}
                    RETURNING id, name, slug, owner_api_key_id, tier, stripe_customer_id, 
                              max_members, settings, created_at, updated_at"""
        
        org = await pool.fetchrow(query, *params)
        
        if not org:
            raise ValueError(f"Organization {org_id} not found")
        
        logger.info(f"Updated organization {org_id}")
        return dict(org)
    
    except Exception as e:
        logger.error(f"Error updating organization {org_id}: {e}")
        raise


async def add_member(org_id: str, api_key_id: str, role: str = "member", 
                     invited_by: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a member to the organization.
    
    Args:
        org_id: Organization ID
        api_key_id: API key ID of the member
        role: Role (member, admin, owner, viewer)
        invited_by: API key ID of the person who invited (optional)
    
    Returns:
        Member dict
    """
    pool = await get_pool()
    
    # Validate role
    valid_roles = ["owner", "admin", "member", "viewer"]
    if role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Must be one of {valid_roles}")
    
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Check if member already exists
                existing = await conn.fetchrow(
                    "SELECT id FROM org_members WHERE org_id = $1 AND api_key_id = $2",
                    org_id, api_key_id
                )
                
                if existing:
                    raise ValueError(f"API key {api_key_id} is already a member of organization {org_id}")
                
                # Add member
                member = await conn.fetchrow(
                    """INSERT INTO org_members (org_id, api_key_id, role, invited_by, joined_at)
                       VALUES ($1, $2, $3, $4, NOW())
                       RETURNING id, org_id, api_key_id, role, invited_by, joined_at""",
                    org_id, api_key_id, role, invited_by
                )
                
                # Update api_keys to assign org_id
                await conn.execute(
                    "UPDATE api_keys SET org_id = $1 WHERE id = $2",
                    org_id, api_key_id
                )
        
        logger.info(f"Added {api_key_id} to organization {org_id} with role '{role}'")
        return dict(member)
    
    except Exception as e:
        if "IntegrityError" in str(type(e)) or "already a member" in str(e):
            logger.error(f"Cannot add member: {e}")
            raise ValueError(f"Cannot add member: {e}")
        logger.error(f"Error adding member {api_key_id} to organization {org_id}: {e}")
        raise


async def remove_member(org_id: str, api_key_id: str) -> bool:
    """
    Remove a member from the organization.
    
    Args:
        org_id: Organization ID
        api_key_id: API key ID of the member to remove
    
    Returns:
        True if member was removed, False if member didn't exist
    """
    pool = await get_pool()
    
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Remove member
                result = await conn.execute(
                    "DELETE FROM org_members WHERE org_id = $1 AND api_key_id = $2",
                    org_id, api_key_id
                )
                
                # Check if member was removed (result is a string like "DELETE 1")
                removed = result != "DELETE 0"
                
                if removed:
                    # Clear org_id from api_keys
                    await conn.execute(
                        "UPDATE api_keys SET org_id = NULL WHERE id = $1",
                        api_key_id
                    )
                    logger.info(f"Removed {api_key_id} from organization {org_id}")
        
        return removed
    
    except Exception as e:
        logger.error(f"Error removing member {api_key_id} from organization {org_id}: {e}")
        raise


async def update_member_role(org_id: str, api_key_id: str, new_role: str) -> Dict[str, Any]:
    """
    Update a member's role in the organization.
    
    Args:
        org_id: Organization ID
        api_key_id: API key ID of the member
        new_role: New role (owner, admin, member, viewer)
    
    Returns:
        Updated member dict
    """
    pool = await get_pool()
    
    # Validate role
    valid_roles = ["owner", "admin", "member", "viewer"]
    if new_role not in valid_roles:
        raise ValueError(f"Invalid role '{new_role}'. Must be one of {valid_roles}")
    
    try:
        member = await pool.fetchrow(
            """UPDATE org_members SET role = $1
               WHERE org_id = $2 AND api_key_id = $3
               RETURNING id, org_id, api_key_id, role, invited_by, joined_at""",
            new_role, org_id, api_key_id
        )
        
        if not member:
            raise ValueError(f"Member {api_key_id} not found in organization {org_id}")
        
        logger.info(f"Updated member role to '%s' in organization %s", new_role, org_id)
        return dict(member)
    
    except Exception as e:
        logger.error("Error updating member role in organization %s: %s", org_id, e)
        raise


async def delete_organization(org_id: str) -> bool:
    """
    Delete an organization and all its members.
    
    Args:
        org_id: Organization ID
    
    Returns:
        True if organization was deleted, False if not found
    """
    pool = await get_pool()
    
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Get all members to clear their org_id
                members = await conn.fetch(
                    "SELECT api_key_id FROM org_members WHERE org_id = $1",
                    org_id
                )
                
                # Delete members
                await conn.execute(
                    "DELETE FROM org_members WHERE org_id = $1",
                    org_id
                )
                
                # Clear org_id from api_keys for all members
                for member in members:
                    await conn.execute(
                        "UPDATE api_keys SET org_id = NULL WHERE id = $1",
                        member["api_key_id"]
                    )
                
                # Delete organization
                result = await conn.execute(
                    "DELETE FROM organizations WHERE id = $1",
                    org_id
                )
                
                deleted = result != "DELETE 0"
                
                if deleted:
                    logger.info(f"Deleted organization {org_id} and removed {len(members)} members")
        
        return deleted
    
    except Exception as e:
        logger.error(f"Error deleting organization {org_id}: {e}")
        raise
