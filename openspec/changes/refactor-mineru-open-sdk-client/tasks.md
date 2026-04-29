## 1. Dependency and Configuration

- [x] 1.1 Add `mineru-open-sdk` dependency through `uv` and update project dependency files
- [x] 1.2 Extend `FullPipelineConfig` with MinerU provider mode, SDK base URL/token env, extra formats, and source handling options
- [x] 1.3 Update `services/profiles/full_pipeline_config.yaml` with documented MinerU provider settings

## 2. Provider Abstraction

- [x] 2.1 Split MinerU client contracts into a provider module with normalized `ParseResult`
- [x] 2.2 Move or adapt the current v4 URL implementation behind a `legacy_v4` provider
- [x] 2.3 Implement a provider factory that validates provider mode and builds the selected provider

## 3. Open SDK Provider

- [x] 3.1 Implement `OpenSdkMinerUClient` using official `mineru-open-sdk`
- [x] 3.2 Normalize SDK results into the project `ParseResult` contract
- [x] 3.3 Save SDK artifacts into the task `extract_dir`, including Markdown and raw debug metadata
- [x] 3.4 Preserve progress callback behavior with page progress when available and coarse state fallback when unavailable

## 4. Document Input Resolution

- [x] 4.1 Add a document input resolver for HTTP URL, storage object key, and local file sources
- [x] 4.2 Materialize storage provider objects into `workspaces/{task_id}/input/`
- [x] 4.3 Validate supported source types and file existence with clear task failure messages

## 5. Pipeline Integration

- [x] 5.1 Update `services/api/task_processor.py` to use the MinerU provider factory and input resolver
- [x] 5.2 Update `FullPipelineService` to use the MinerU provider factory
- [x] 5.3 Keep existing public `document_url` task submission flow backward compatible
- [x] 5.4 Ensure existing artifact persistence still stores MinerU extracted outputs from SDK mode

## 6. Validation

- [x] 6.1 Add unit tests for provider factory and unsupported provider configuration
- [x] 6.2 Add unit tests for input resolver URL, storage key, and local path scenarios
- [x] 6.3 Add normalization tests for Open SDK result objects using mocked SDK responses
- [x] 6.4 Run backend tests with `uv run pytest`
- [x] 6.5 Manually validate one URL document through `open_sdk` mode when credentials/network are available
- [x] 6.6 Manually validate one storage object input through `open_sdk` mode when MinIO/storage data is available

## 7. Documentation and Tracking

- [x] 7.1 Update README/services docs with MinerU provider mode and MinIO input behavior
- [x] 7.2 Seed Beads issues from this OpenSpec after user approval
- [x] 7.3 Update this OpenSpec checklist as implementation tasks complete
