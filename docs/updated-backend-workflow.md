# Updated GitHub Actions Workflow: `.github/workflows/backend.yml`

Copy the YAML below and paste it into your `.github/workflows/backend.yml` file on GitHub.

## What Changed and Why

1. **Added environment variables** - The app imports modules that reference `DATABASE_URL`, `API_SECRET_KEY`, and `NVIDIA_NIM_API_KEY` at startup. Without these set (even to dummy values), middleware and billing code can fail during test collection when `main.py` is imported.
2. **Added `PYTHONPATH`** - Ensures pytest can resolve `app.*` imports from the backend directory without relying solely on `pytest.ini`.
3. **Removed redundant `pip install pytest httpx`** - Both are already in `requirements.txt`.
4. **Removed `pytest --collect-only || exit 0` guard** - This was masking real failures by exiting with success if collection failed.
5. **Added `cache-dependency-path`** - Points pip cache to the actual requirements file for faster CI runs.
6. **Added `-v --tb=short` flags** - Better test output for diagnosing failures in CI logs.

## Updated Workflow

```yaml
name: Backend CI/CD
permissions:
  contents: read

on:
  push:
    branches: [ main ]
    paths: [ 'amaima/backend/**' ]
  pull_request:
    branches: [ main ]
    paths: [ 'amaima/backend/**' ]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: ""
      API_SECRET_KEY: "test_secret_key_for_ci"
      NVIDIA_NIM_API_KEY: "test_nim_key_for_ci"
      PYTHONPATH: "."
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: amaima/backend/requirements.txt
      - name: Install dependencies
        run: |
          cd amaima/backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd amaima/backend
          pytest tests/ -v --tb=short
```

## Supporting Files

These files in the codebase support the CI pipeline:

- **`amaima/backend/requirements.txt`** - Includes `pytest`, `pytest-asyncio`, and `httpx` in the dependencies.
- **`amaima/backend/pytest.ini`** - Configured with `asyncio_mode = auto`, `pythonpath = .`, and `testpaths = tests`.
- **`amaima/backend/conftest.py`** - Adds the backend directory to `sys.path` for module resolution.

## Notes

- **63 total tests**: 55 unit tests (routing, agents, crews, workflows) + 8 integration tests (full app endpoints, caching, rate limiting).
- All tests use mocks for external services (NVIDIA NIM API, database calls) so no live services are needed in CI.
- The environment variables (`DATABASE_URL`, `API_SECRET_KEY`, `NVIDIA_NIM_API_KEY`) are set to dummy values so the app can import cleanly without connecting to real services.
- `PYTHONPATH: "."` ensures pytest resolves `app.*` imports from the backend directory.

# Backend CI/CD
Add audio and image generation capabilities to the AI agent #80
All jobs
Run details
Annotations
1 error
test
failed 2 hours ago in 23s
Search logs
0s
5s
2s
12s
1s
Run cd amaima/backend
  cd amaima/backend
  pytest tests/ -v --tb=short
  shell: /usr/bin/bash -e {0}
  env:
    DATABASE_URL: 
    API_SECRET_KEY: test_secret_key_for_ci
    NVIDIA_NIM_API_KEY: test_nim_key_for_ci
    PYTHONPATH: .
    pythonLocation: /opt/hostedtoolcache/Python/3.11.14/x64
    PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.14/x64/lib/pkgconfig
    Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
    Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
    Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.14/x64
    LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.14/x64/lib
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /opt/hostedtoolcache/Python/3.11.14/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/AMAIMA/AMAIMA/amaima/backend
configfile: pytest.ini
plugins: asyncio-1.3.0, anyio-4.12.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 63 items

tests/agents/test_biology_crew.py::TestBiologyAgentRoles::test_molecule_generator PASSED [  1%]
tests/agents/test_biology_crew.py::TestBiologyAgentRoles::test_admet_predictor PASSED [  3%]
tests/agents/test_biology_crew.py::TestBiologyAgentRoles::test_lead_optimizer PASSED [  4%]
tests/agents/test_biology_crew.py::TestBiologyAgentRoles::test_safety_reviewer PASSED [  6%]
tests/agents/test_biology_crew.py::TestDrugDiscoveryCrew::test_run_drug_discovery_crew PASSED [  7%]
tests/agents/test_biology_crew.py::TestDrugDiscoveryCrew::test_drug_discovery_default_properties PASSED [  9%]
tests/agents/test_biology_crew.py::TestDrugDiscoveryCrew::test_drug_discovery_error_handling PASSED [ 11%]
tests/agents/test_biology_crew.py::TestProteinAnalysisCrew::test_run_protein_analysis_crew PASSED [ 12%]
tests/agents/test_biology_crew.py::TestProteinAnalysisCrew::test_protein_analysis_short_sequence PASSED [ 14%]
tests/agents/test_crew_manager.py::TestAgentRole::test_init PASSED       [ 15%]
tests/agents/test_crew_manager.py::TestAgentRole::test_default_model PASSED [ 17%]
tests/agents/test_crew_manager.py::TestAgentRole::test_execute_success PASSED [ 19%]
tests/agents/test_crew_manager.py::TestAgentRole::test_execute_with_context PASSED [ 20%]
tests/agents/test_crew_manager.py::TestAgentRole::test_execute_error PASSED [ 22%]
tests/agents/test_crew_manager.py::TestAgentRole::test_memory_accumulation PASSED [ 23%]
tests/agents/test_crew_manager.py::TestCrew::test_sequential_process PASSED [ 25%]
tests/agents/test_crew_manager.py::TestCrew::test_parallel_process PASSED [ 26%]
tests/agents/test_crew_manager.py::TestCrew::test_hierarchical_process PASSED [ 28%]
tests/agents/test_crew_manager.py::TestResearchCrew::test_run_research_crew PASSED [ 30%]
tests/agents/test_crew_manager.py::TestCustomCrew::test_run_custom_crew PASSED [ 31%]
tests/agents/test_langchain_agent.py::TestWorkflowState::test_init PASSED [ 33%]
tests/agents/test_langchain_agent.py::TestWorkflowState::test_add_message PASSED [ 34%]
tests/agents/test_langchain_agent.py::TestWorkflowState::test_context_operations PASSED [ 36%]
tests/agents/test_langchain_agent.py::TestWorkflowNode::test_init PASSED [ 38%]
tests/agents/test_langchain_agent.py::TestWorkflowNode::test_execute PASSED [ 39%]
tests/agents/test_langchain_agent.py::TestWorkflowNode::test_execute_error PASSED [ 41%]
tests/agents/test_langchain_agent.py::TestConditionalEdge::test_true_condition PASSED [ 42%]
tests/agents/test_langchain_agent.py::TestConditionalEdge::test_false_condition PASSED [ 44%]
tests/agents/test_langchain_agent.py::TestConditionalEdge::test_exception_defaults_to_false PASSED [ 46%]
tests/agents/test_langchain_agent.py::TestStatefulWorkflow::test_simple_workflow PASSED [ 47%]
tests/agents/test_langchain_agent.py::TestStatefulWorkflow::test_no_entry_point PASSED [ 49%]
tests/agents/test_langchain_agent.py::TestStatefulWorkflow::test_missing_node PASSED [ 50%]
tests/agents/test_langchain_agent.py::TestStatefulWorkflow::test_conditional_workflow PASSED [ 52%]
tests/agents/test_langchain_agent.py::TestStatefulWorkflow::test_max_iterations PASSED [ 53%]
tests/agents/test_langchain_agent.py::TestStatefulWorkflow::test_with_context PASSED [ 55%]
tests/agents/test_langchain_agent.py::TestBuiltInWorkflows::test_research_workflow PASSED [ 57%]
tests/agents/test_langchain_agent.py::TestBuiltInWorkflows::test_complex_reasoning_workflow PASSED [ 58%]
tests/agents/test_langchain_agent.py::TestBuiltInWorkflows::test_domain_workflow_biology PASSED [ 60%]
tests/agents/test_langchain_agent.py::TestBuiltInWorkflows::test_domain_workflow_robotics PASSED [ 61%]
tests/agents/test_langchain_agent.py::TestBuiltInWorkflows::test_domain_workflow_vision PASSED [ 63%]
tests/agents/test_langchain_agent.py::TestRunLangchainAgent::test_run_research PASSED [ 65%]
tests/agents/test_langchain_agent.py::TestRunLangchainAgent::test_run_unknown_type PASSED [ 66%]
tests/agents/test_langchain_agent.py::TestRunLangchainAgent::test_workflow_registry PASSED [ 68%]
tests/agents/test_langchain_agent.py::TestListWorkflows::test_list_workflows FAILED [ 69%]
tests/agents/test_robotics_crew.py::TestRoboticsAgentRoles::test_perception_agent PASSED [ 71%]
tests/agents/test_robotics_crew.py::TestRoboticsAgentRoles::test_path_planner PASSED [ 73%]
tests/agents/test_robotics_crew.py::TestRoboticsAgentRoles::test_action_executor PASSED [ 74%]
tests/agents/test_robotics_crew.py::TestRoboticsAgentRoles::test_safety_monitor PASSED [ 76%]
tests/agents/test_robotics_crew.py::TestNavigationCrew::test_run_navigation_crew PASSED [ 77%]
tests/agents/test_robotics_crew.py::TestNavigationCrew::test_navigation_defaults PASSED [ 79%]
tests/agents/test_robotics_crew.py::TestNavigationCrew::test_navigation_error PASSED [ 80%]
tests/agents/test_robotics_crew.py::TestManipulationCrew::test_run_manipulation_crew PASSED [ 82%]
tests/agents/test_robotics_crew.py::TestManipulationCrew::test_manipulation_default_object PASSED [ 84%]
tests/agents/test_robotics_crew.py::TestSwarmCrew::test_run_swarm_crew PASSED [ 85%]
tests/agents/test_robotics_crew.py::TestSwarmCrew::test_swarm_defaults PASSED [ 87%]
tests/integration/test_biology_e2e.py::test_biology_discover_endpoint PASSED [ 88%]
tests/integration/test_biology_e2e.py::test_biology_drug_discovery_crew PASSED [ 90%]
tests/integration/test_biology_e2e.py::test_biology_protein_analysis_crew PASSED [ 92%]
tests/integration/test_biology_e2e.py::test_biology_crew_sequential_pipeline PASSED [ 93%]
tests/integration/test_biology_e2e.py::test_agent_types_endpoint PASSED  [ 95%]
tests/integration/test_biology_e2e.py::test_nim_cache_stats PASSED       [ 96%]
tests/integration/test_biology_e2e.py::test_nim_prompt_cache_functionality PASSED [ 98%]
tests/integration/test_biology_e2e.py::test_mau_rate_limit_middleware PASSED [100%]

=================================== FAILURES ===================================
____________________ TestListWorkflows.test_list_workflows _____________________
tests/agents/test_langchain_agent.py:242: in test_list_workflows
    assert len(workflows) == 5
E   AssertionError: assert 7 == 5
E    +  where 7 = len([{'description': 'Multi-step research with analysis and synthesis', 'id': 'research', 'name': 'Research Workflow'}, {'description': 'Problem decomposition with iterative validation', 'id': 'complex_reasoning', 'name': 'Complex Reasoning'}, {'description': 'Domain-specific biology analysis with peer review', 'id': 'biology', 'name': 'Biology Research'}, {'description': 'Robot task planning with safety validation', 'id': 'robotics', 'name': 'Robotics Planning'}, {'description': 'Visual reasoning with structured analysis', 'id': 'vision', 'name': 'Vision Analysis'}, {'description': 'Neural speech synthesis and emotional tone analysis', 'id': 'audio', 'name': 'Audio Synthesis'}, ...])
=============================== warnings summary ===============================
tests/integration/test_biology_e2e.py::test_biology_discover_endpoint
  /home/runner/work/AMAIMA/AMAIMA/amaima/backend/main.py:137: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

tests/integration/test_biology_e2e.py::test_biology_discover_endpoint
  /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages/fastapi/applications.py:4597: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    return self.router.on_event(event_type)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/agents/test_langchain_agent.py::TestListWorkflows::test_list_workflows - AssertionError: assert 7 == 5
 +  where 7 = len([{'description': 'Multi-step research with analysis and synthesis', 'id': 'research', 'name': 'Research Workflow'}, {'description': 'Problem decomposition with iterative validation', 'id': 'complex_reasoning', 'name': 'Complex Reasoning'}, {'description': 'Domain-specific biology analysis with peer review', 'id': 'biology', 'name': 'Biology Research'}, {'description': 'Robot task planning with safety validation', 'id': 'robotics', 'name': 'Robotics Planning'}, {'description': 'Visual reasoning with structured analysis', 'id': 'vision', 'name': 'Vision Analysis'}, {'description': 'Neural speech synthesis and emotional tone analysis', 'id': 'audio', 'name': 'Audio Synthesis'}, ...])
=================== 1 failed, 62 passed, 2 warnings in 0.83s ===================
Error: Process completed with exit code 1.
0s
1s
0s
