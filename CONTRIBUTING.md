# Contributing to Jub

First off, thank you for contributing to the MADTEC-2025-M-478 project! As part of the development team for Jub (Prod1E1-C1/C2), your work helps build a national infrastructure for strategic data.

To maintain the quality of our software and ensure compliance with project requirements, please follow these guidelines.

## Development workflow
We use a standard Feature Branch workflow. Please do not push directly to the `master` branch.

1. Sync your fork: Ensure your local `master` is up to date with the upstream repository.

2. Create a branch: Use a descriptive name:

    - feature/new-indexing-logic

    - fix/api-connection-timeout

    - docs/update-readme-examples

3. Develop: Write your code, following the style guides below.

4. Test: Run existing tests (e.g., pytest for the Client/API) and add new ones for your features.

5. Pull Request: Open a PR to the `master` branch. Describe exactly what your changes do.

## ⚖️ Mandatory license headers

**Every new source file MUST start with the Apache 2.0 License header.** This is a non-negotiable requirement for the government project and future patenting.

### Python header
Copy and paste this at the top of every `.py` file:

```python
# Copyright 2026 MADTEC-2025-M-478 Project Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```