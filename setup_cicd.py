"""
MAOS v6.0 - GitHub Actions CI/CD配置
"""

workflow_content = """
name: MAOS CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio coverage
    
    - name: Run tests
      run: |
        pytest maos/tests/ -v --cov=maos --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t maos:${{ github.sha }} .
        docker tag maos:${{ github.sha }} maos:latest
    
    - name: Run integration tests
      run: |
        docker-compose up -d
        sleep 10
        # Add integration test commands here
        docker-compose down

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        echo "Deploying MAOS v6.0 to production..."
        # Add deployment commands here
"""

import os

# 创建GitHub workflows目录
workflow_dir = ".github/workflows"
os.makedirs(workflow_dir, exist_ok=True)

# 写入CI/CD配置
ci_file = os.path.join(workflow_dir, "ci.yml")
with open(ci_file, "w") as f:
    f.write(workflow_content)

print("✅ GitHub Actions CI/CD configuration created!")
print(f"📁 File: {ci_file}")
