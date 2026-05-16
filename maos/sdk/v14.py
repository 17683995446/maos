"""
MAOS v14.0 - Multi-Language SDK Framework
多语言 SDK 框架 - 支持 Python/JS/Go/Java/Rust
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json


class MockSession:
    """Mock session for testing without requests library"""
    
    def __init__(self):
        self.headers = {}
    
    def request(self, method, url, json=None, params=None, timeout=None):
        """Mock request that returns sample data"""
        class MockResponse:
            def __init__(self, data):
                self._data = data
            
            def json(self):
                return {"data": self._data, "message": "Success"}
            
            def raise_for_status(self):
                pass
        
        # Mock responses based on endpoint
        if "/workflows" in url and method == "GET":
            return MockResponse([{"id": "wf-1", "name": "Test Workflow"}])
        elif "/workflows" in url and method == "POST":
            return MockResponse({"id": str(uuid.uuid4()), "name": json.get("name", "New Workflow")})
        elif "/workflows/" in url and "/execute" in url:
            return MockResponse({
                "execution_id": str(uuid.uuid4()),
                "status": "completed",
                "output_data": json.get("input_data", {}),
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            })
        else:
            return MockResponse({"status": "ok"})


class RealHTTPSession:
    """Real HTTP session using requests library"""
    
    def __init__(self):
        try:
            import requests
            self._requests = requests
            self._session = requests.Session()
            self._real = True
        except ImportError:
            self._real = False
            self._session = None
    
    @property
    def headers(self) -> Dict[str, str]:
        if self._real:
            return self._session.headers
        return {}
    
    def _set_headers(self, headers: Dict[str, str]) -> None:
        """Set headers on the session"""
        if self._real:
            self._session.headers.update(headers)
    
    def request(self, method, url, json=None, params=None, timeout=None):
        """Real HTTP request"""
        if not self._real:
            raise ImportError("requests library not installed. Install with: pip install requests")
        
        class RealResponse:
            def __init__(self, response):
                self._response = response
            
            def json(self):
                return self._response.json()
            
            def raise_for_status(self):
                self._response.raise_for_status()
        
        response = self._session.request(
            method=method,
            url=url,
            json=json,
            params=params,
            timeout=timeout or 30
        )
        return RealResponse(response)


class SDKLanguage(Enum):
    """SDK语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    GO = "go"
    JAVA = "java"
    RUST = "rust"


class APIResponseStatus(Enum):
    """API响应状态"""
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class SDKConfig:
    """SDK配置"""
    api_key: str = ""
    base_url: str = "https://api.maos.ai/v1"
    timeout: int = 30
    retries: int = 3
    debug: bool = False
    language: SDKLanguage = SDKLanguage.PYTHON


@dataclass
class APIResponse(Generic[TypeVar('T')]):
    """API响应"""
    status: APIResponseStatus
    data: T = None
    error: Optional[str] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_success(self) -> bool:
        return self.status == APIResponseStatus.SUCCESS


@dataclass
class WorkflowCreateRequest:
    """工作流创建请求"""
    name: str
    description: str = ""
    version: str = "1.0"
    steps: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecutionRequest:
    """工作流执行请求"""
    workflow_id: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    sync: bool = True
    timeout: int = 300


@dataclass
class ExecutionResult:
    """执行结果"""
    execution_id: str
    status: str
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BaseSDK:
    """基础SDK类"""
    
    def __init__(self, config: SDKConfig):
        self.config = config
        
        # Try to use real HTTP session if requests is available
        try:
            self._session = RealHTTPSession()
            self._real_http = True
        except ImportError:
            # Fall back to mock session
            self._session = MockSession()
            self._real_http = False
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        if hasattr(self._session, '_set_headers'):
            self._session._set_headers(headers)
        else:
            self._session.headers = headers
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> APIResponse:
        """发起API请求"""
        url = f"{self.config.base_url}{endpoint}"
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return APIResponse(
                status=APIResponseStatus.SUCCESS,
                data=result.get("data"),
                message=result.get("message", "Success")
            )
        
        except requests.exceptions.RequestException as e:
            return APIResponse(
                status=APIResponseStatus.ERROR,
                error=str(e),
                message="Request failed"
            )
    
    def _handle_response(self, response: APIResponse) -> Any:
        """处理响应"""
        if response.is_success():
            return response.data
        raise Exception(f"API Error: {response.error} - {response.message}")


class MAOSSDK(BaseSDK):
    """MAOS SDK主类"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.maos.ai/v1"):
        config = SDKConfig(api_key=api_key, base_url=base_url)
        super().__init__(config)
    
    def create_workflow(self, request: WorkflowCreateRequest) -> Dict[str, Any]:
        """创建工作流"""
        response = self._request(
            method="POST",
            endpoint="/workflows",
            data={
                "name": request.name,
                "description": request.description,
                "version": request.version,
                "steps": request.steps,
                "metadata": request.metadata
            }
        )
        return self._handle_response(response)
    
    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流"""
        response = self._request(
            method="GET",
            endpoint=f"/workflows/{workflow_id}"
        )
        return self._handle_response(response)
    
    def list_workflows(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """列出工作流"""
        response = self._request(
            method="GET",
            endpoint="/workflows",
            params={"page": page, "limit": limit}
        )
        return self._handle_response(response)
    
    def update_workflow(self, workflow_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新工作流"""
        response = self._request(
            method="PUT",
            endpoint=f"/workflows/{workflow_id}",
            data=data
        )
        return self._handle_response(response)
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        response = self._request(
            method="DELETE",
            endpoint=f"/workflows/{workflow_id}"
        )
        if response.is_success():
            return True
        return False
    
    def execute_workflow(self, request: WorkflowExecutionRequest) -> ExecutionResult:
        """执行工作流"""
        response = self._request(
            method="POST",
            endpoint=f"/workflows/{request.workflow_id}/execute",
            data={
                "input_data": request.input_data,
                "sync": request.sync,
                "timeout": request.timeout
            }
        )
        data = self._handle_response(response)
        
        return ExecutionResult(
            execution_id=data.get("execution_id"),
            status=data.get("status"),
            output_data=data.get("output_data", {}),
            error=data.get("error"),
            started_at=datetime.fromisoformat(data.get("started_at")) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data.get("completed_at")) if data.get("completed_at") else None
        )
    
    def get_execution(self, execution_id: str) -> ExecutionResult:
        """获取执行结果"""
        response = self._request(
            method="GET",
            endpoint=f"/executions/{execution_id}"
        )
        data = self._handle_response(response)
        
        return ExecutionResult(
            execution_id=data.get("execution_id"),
            status=data.get("status"),
            output_data=data.get("output_data", {}),
            error=data.get("error"),
            started_at=datetime.fromisoformat(data.get("started_at")) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data.get("completed_at")) if data.get("completed_at") else None
        )


class SDKGenerator:
    """SDK代码生成器"""
    
    LANGUAGE_TEMPLATES = {
        SDKLanguage.PYTHON: {
            "class": """class {class_name}:
    def __init__(self, api_key: str, base_url: str = "{base_url}"):
        self.client = MAOSSDK(api_key, base_url)
    
    {methods}""",
            "method": """    def {method_name}(self{params}) -> {return_type}:
        \"\"\"{docstring}\"\"\"
        {body}"""
        },
        SDKLanguage.JAVASCRIPT: {
            "class": """class {class_name} {{
  constructor(apiKey, baseUrl = "{base_url}") {{
    this.client = new MAOSSDK(apiKey, baseUrl);
  }}
  
  {methods}
}}""",
            "method": """  {method_name}({params}) {{
    // {docstring}
    {body}
  }}"""
        },
        SDKLanguage.GO: {
            "class": """type {class_name} struct {{
    client *MAOSSDK
}}

func New{class_name}(apiKey string, baseURL ...string) *{class_name} {{
    url := "{base_url}"
    if len(baseURL) > 0 {{
        url = baseURL[0]
    }}
    return &{class_name}{{
        client: NewMAOSSDK(apiKey, url),
    }}
}}

{methods}""",
            "method": """func (s *MAOSClient) {method_name}({params}) {return_type} {{
    // {docstring}
    {body}
}}"""
        },
        SDKLanguage.JAVA: {
            "class": """public class {class_name} {{
    private final MAOSSDK client;
    
    public {class_name}(String apiKey) {{
        this(apiKey, "{base_url}");
    }}
    
    public {class_name}(String apiKey, String baseUrl) {{
        this.client = new MAOSSDK(apiKey, baseUrl);
    }}
    
    {methods}
}}""",
            "method": """    public {return_type} {method_name}({params}) {{
        // {docstring}
        {body}
    }}"""
        },
        SDKLanguage.RUST: {
            "class": """pub struct {class_name} {{
    client: MAOSSDK,
}}

impl {class_name} {{
    pub fn new(api_key: &str) -> Self {{
        Self {{
            client: MAOSSDK::new(api_key, "{base_url}"),
        }}
    }}
    
    pub fn new_with_url(api_key: &str, base_url: &str) -> Self {{
        Self {{
            client: MAOSSDK::new(api_key, base_url),
        }}
    }}
    
    {methods}
}}""",
            "method": """    pub async fn {method_name}(&self{params}) -> Result<{return_type}, Error> {{
        // {docstring}
        {body}
    }}"""
        }
    }
    
    def __init__(self, language: SDKLanguage):
        self.language = language
    
    def generate_client(self, class_name: str = "MAOSClient") -> str:
        """生成客户端代码"""
        template = self.LANGUAGE_TEMPLATES.get(self.language)
        if not template:
            raise ValueError(f"Unsupported language: {self.language}")
        
        methods = self._generate_methods()
        return template["class"].format(
            class_name=class_name,
            base_url="https://api.maos.ai/v1",
            methods=methods
        )
    
    def _generate_methods(self) -> str:
        """生成方法代码"""
        template = self.LANGUAGE_TEMPLATES.get(self.language)
        if not template:
            return ""
        
        method_defs = [
            {
                "name": "create_workflow",
                "docstring": "创建工作流",
                "params": {
                    SDKLanguage.PYTHON: ", name: str, description: str = \"\", version: str = \"1.0\", steps: List[Dict] = None",
                    SDKLanguage.JAVASCRIPT: "name, description = \"\", version = \"1.0\", steps = []",
                    SDKLanguage.GO: "name string, description string, version string, steps []map[string]interface{}",
                    SDKLanguage.JAVA: "String name, String description, String version, List<Map<String, Object>> steps",
                    SDKLanguage.RUST: ", name: &str, description: &str, version: &str, steps: Vec<serde_json::Value>"
                },
                "return_type": {
                    SDKLanguage.PYTHON: "Dict[str, Any]",
                    SDKLanguage.JAVASCRIPT: "Promise<Object>",
                    SDKLanguage.GO: "map[string]interface{}",
                    SDKLanguage.JAVA: "Map<String, Object>",
                    SDKLanguage.RUST: "serde_json::Value"
                },
                "body": {
                    SDKLanguage.PYTHON: "return self.client.create_workflow(WorkflowCreateRequest(name=name, description=description, version=version, steps=steps or []))",
                    SDKLanguage.JAVASCRIPT: "return this.client.createWorkflow({ name, description, version, steps });",
                    SDKLanguage.GO: "return s.client.CreateWorkflow(name, description, version, steps)",
                    SDKLanguage.JAVA: "return client.createWorkflow(name, description, version, steps);",
                    SDKLanguage.RUST: "self.client.create_workflow(name, description, version, steps).await"
                }
            },
            {
                "name": "execute_workflow",
                "docstring": "执行工作流",
                "params": {
                    SDKLanguage.PYTHON: ", workflow_id: str, input_data: Dict = None, sync: bool = True",
                    SDKLanguage.JAVASCRIPT: "workflowId, inputData = {}, sync = true",
                    SDKLanguage.GO: "workflowID string, inputData map[string]interface{}, sync bool",
                    SDKLanguage.JAVA: "String workflowId, Map<String, Object> inputData, boolean sync",
                    SDKLanguage.RUST: ", workflow_id: &str, input_data: serde_json::Value, sync: bool"
                },
                "return_type": {
                    SDKLanguage.PYTHON: "ExecutionResult",
                    SDKLanguage.JAVASCRIPT: "Promise<ExecutionResult>",
                    SDKLanguage.GO: "ExecutionResult",
                    SDKLanguage.JAVA: "ExecutionResult",
                    SDKLanguage.RUST: "ExecutionResult"
                },
                "body": {
                    SDKLanguage.PYTHON: "return self.client.execute_workflow(WorkflowExecutionRequest(workflow_id=workflow_id, input_data=input_data or {}, sync=sync))",
                    SDKLanguage.JAVASCRIPT: "return this.client.executeWorkflow({ workflowId, inputData, sync });",
                    SDKLanguage.GO: "return s.client.ExecuteWorkflow(workflowID, inputData, sync)",
                    SDKLanguage.JAVA: "return client.executeWorkflow(workflowId, inputData, sync);",
                    SDKLanguage.RUST: "self.client.execute_workflow(workflow_id, input_data, sync).await"
                }
            }
        ]
        
        methods = []
        for method in method_defs:
            methods.append(template["method"].format(
                method_name=method["name"],
                params=method["params"].get(self.language, ""),
                return_type=method["return_type"].get(self.language, "void"),
                docstring=method["docstring"],
                body=method["body"].get(self.language, "")
            ))
        
        return "\n\n".join(methods)


class SDKFactory:
    """SDK工厂"""
    
    @staticmethod
    def create(language: SDKLanguage, api_key: str, base_url: str = None) -> MAOSSDK:
        """创建SDK实例"""
        url = base_url or "https://api.maos.ai/v1"
        return MAOSSDK(api_key, url)
    
    @staticmethod
    def generate_code(language: SDKLanguage, output_path: str = None) -> str:
        """生成SDK代码"""
        generator = SDKGenerator(language)
        code = generator.generate_client()
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(code)
        
        return code
