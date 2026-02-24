package com.amaima.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.amaima.app.data.local.entity.QueryEntity
import com.amaima.app.data.local.dao.*

@Database(entities = [QueryEntity::class], version = 1, exportSchema = false)
abstract class AmaimaDatabase : RoomDatabase() {
    abstract fun queryDao(): QueryDao
    abstract fun workflowDao(): WorkflowDao
    abstract fun userDao(): UserDao
}
