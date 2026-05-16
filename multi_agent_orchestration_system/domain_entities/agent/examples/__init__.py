"""
Domain Entities - Agent Examples Module
======================================

Provides concrete agent implementations demonstrating the agent framework.
These agents serve as reference implementations and can be customized for specific use cases.

Available Agents:
  - DataProcessingAgent: Handles data cleaning, transformation, and validation
  - DataAnalysisAgent: Performs statistical analysis and pattern recognition
  - ReportGenerationAgent: Generates reports and summaries in various formats
  - Custom agents can be created by extending BaseAgent
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from multi_agent_orchestration_system.core_abstractions import (
    BaseAgent,
    AgentMessage,
    AgentMessagePayload,
    AgentMessageType,
    AgentCapabilities
)


class DataProcessingAgent(BaseAgent):
    """
    Specialized agent for data processing operations.
    
    Capabilities:
      - data_cleaning: Remove null/empty values, standardize formats
      - data_transformation: Format conversions, normalization
      - data_validation: Schema validation, data quality checks
      - data_aggregation: Grouping, summarizing, pivot operations
    
    Example Use Cases:
      - ETL pipelines
      - Data quality assurance
      - Format standardization
    """
    
    def __init__(self, agent_name: str = "data_processing_agent"):
        super().__init__(
            agent_name=agent_name,
            agent_description="Specialized agent for data processing and cleaning operations",
            capability_list=[
                "data_cleaning",
                "data_transformation",
                "data_validation",
                "data_aggregation",
                "data_format_conversion"
            ]
        )
        self.processed_records_total_count = 0
        self.cleaning_operations_count = 0
    
    def process_task_request(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process data processing task request"""
        if message.payload is None:
            return self._create_error_response(message, "No payload provided")
        
        input_data = message.payload.data_content
        processing_operation = message.metadata.get('operation', 'clean')
        
        try:
            if processing_operation == 'clean':
                processed_result = self._execute_data_cleaning_operation(input_data)
            elif processing_operation == 'transform':
                processed_result = self._execute_data_transformation_operation(input_data)
            elif processing_operation == 'validate':
                processed_result = self._execute_data_validation_operation(input_data)
            elif processing_operation == 'aggregate':
                processed_result = self._execute_data_aggregation_operation(input_data)
            else:
                processed_result = self._execute_data_cleaning_operation(input_data)
            
            self.processed_records_total_count += self._count_records(processed_result)
            self.cleaning_operations_count += 1
            
            response_data = {
                'status': 'success',
                'operation': processing_operation,
                'result': processed_result,
                'processing_metadata': {
                    'records_processed': self.processed_records_total_count,
                    'operations_count': self.cleaning_operations_count,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            return AgentMessage(
                sender_agent_name=self.agent_name,
                receiver_agent_names=[message.sender_agent_name],
                message_type=AgentMessageType.TASK_RESPONSE,
                payload=AgentMessagePayload(data_content=response_data),
                reply_to_message_id=message.message_id
            )
            
        except Exception as error:
            return self._create_error_response(message, str(error))
    
    def _execute_data_cleaning_operation(self, data: Any) -> Any:
        """Execute data cleaning logic"""
        if isinstance(data, dict):
            return self._clean_dictionary_data(data)
        elif isinstance(data, list):
            return [self._clean_dictionary_data(item) 
                   for item in data 
                   if isinstance(item, dict) and self._is_valid_data_record(item)]
        return data
    
    def _execute_data_transformation_operation(self, data: Any) -> Any:
        """Execute data transformation logic"""
        if isinstance(data, dict):
            return self._transform_dictionary_data(data)
        elif isinstance(data, list):
            return [self._transform_dictionary_data(item) for item in data if isinstance(item, dict)]
        return data
    
    def _execute_data_validation_operation(self, data: Any) -> Any:
        """Execute data validation logic"""
        validation_results = {
            'is_valid': True,
            'validation_errors': [],
            'warnings': []
        }
        
        if isinstance(data, dict):
            errors, warnings = self._validate_dictionary_schema(data)
            validation_results['is_valid'] = len(errors) == 0
            validation_results['validation_errors'] = errors
            validation_results['warnings'] = warnings
        elif isinstance(data, list):
            all_errors = []
            all_warnings = []
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    errors, warnings = self._validate_dictionary_schema(item)
                    for error in errors:
                        all_errors.append(f"Item {idx}: {error}")
                    all_warnings.extend([f"Item {idx}: {w}" for w in warnings])
            
            validation_results['is_valid'] = len(all_errors) == 0
            validation_results['validation_errors'] = all_errors
            validation_results['warnings'] = all_warnings
        
        return validation_results
    
    def _execute_data_aggregation_operation(self, data: Any) -> Any:
        """Execute data aggregation logic"""
        if not isinstance(data, list):
            return {'error': 'Aggregation requires list input'}
        
        aggregation_result = {
            'total_records': len(data),
            'numeric_fields_summary': {},
            'categorical_fields_summary': {}
        }
        
        numeric_values = []
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, (int, float)):
                        numeric_values.append(value)
                        if key not in aggregation_result['numeric_fields_summary']:
                            aggregation_result['numeric_fields_summary'][key] = []
                        aggregation_result['numeric_fields_summary'][key].append(value)
        
        if numeric_values:
            aggregation_result['overall_numeric_stats'] = {
                'count': len(numeric_values),
                'sum': sum(numeric_values),
                'mean': sum(numeric_values) / len(numeric_values),
                'min': min(numeric_values),
                'max': max(numeric_values)
            }
        
        return aggregation_result
    
    def _clean_dictionary_data(self, data: Dict) -> Dict:
        """Clean individual dictionary record"""
        cleaned_record = {}
        for field_key, field_value in data.items():
            if field_value is not None and field_value != '':
                if isinstance(field_value, str) and field_value.strip():
                    cleaned_record[field_key] = field_value.strip()
                else:
                    cleaned_record[field_key] = field_value
        return cleaned_record
    
    def _transform_dictionary_data(self, data: Dict) -> Dict:
        """Transform dictionary data"""
        transformed = {}
        for field_key, field_value in data.items():
            if isinstance(field_value, str):
                transformed[field_key] = field_value.lower().strip()
            else:
                transformed[field_key] = field_value
        return transformed
    
    def _validate_dictionary_schema(self, data: Dict) -> tuple:
        """Validate dictionary against schema"""
        errors = []
        warnings = []
        
        for field_key, field_value in data.items():
            if field_value is None:
                warnings.append(f"Field '{field_key}' has null value")
            elif isinstance(field_value, str) and not field_value.strip():
                warnings.append(f"Field '{field_key}' has empty value")
        
        return errors, warnings
    
    def _is_valid_data_record(self, record: Dict) -> bool:
        """Check if record is valid for processing"""
        if not isinstance(record, dict):
            return False
        return any(
            value is not None and value != '' 
            for value in record.values()
        )
    
    def _count_records(self, data: Any) -> int:
        """Count records in data structure"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return 1
        return 0
    
    def _create_error_response(self, message: AgentMessage, error_message: str) -> AgentMessage:
        """Create error response message"""
        return AgentMessage(
            sender_agent_name=self.agent_name,
            receiver_agent_names=[message.sender_agent_name],
            message_type=AgentMessageType.ERROR_NOTIFICATION,
            payload=AgentMessagePayload(data_content={'error': error_message}),
            reply_to_message_id=message.message_id
        )


class DataAnalysisAgent(BaseAgent):
    """
    Specialized agent for data analysis and statistical operations.
    
    Capabilities:
      - statistical_analysis: Descriptive statistics, distributions
      - pattern_recognition: Trends, anomalies, correlations
      - data_visualization_prep: Prepare data for visualization
      - trend_detection: Time series analysis
    
    Example Use Cases:
      - Business intelligence
      - Anomaly detection
      - Trend analysis
      - Predictive analytics preparation
    """
    
    def __init__(self, agent_name: str = "data_analysis_agent"):
        super().__init__(
            agent_name=agent_name,
            agent_description="Specialized agent for statistical analysis and pattern recognition",
            capability_list=[
                "statistical_analysis",
                "pattern_recognition",
                "data_visualization_preparation",
                "trend_detection",
                "correlation_analysis"
            ]
        )
        self.analysis_operations_performed_count = 0
    
    def process_task_request(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process data analysis task request"""
        if message.payload is None:
            return self._create_error_response(message, "No payload provided")
        
        input_data = message.payload.data_content
        analysis_type = message.metadata.get('analysis_type', 'statistics')
        
        try:
            if analysis_type == 'statistics':
                analysis_result = self._perform_statistical_analysis(input_data)
            elif analysis_type == 'patterns':
                analysis_result = self._detect_patterns_and_trends(input_data)
            elif analysis_type == 'correlation':
                analysis_result = self._analyze_correlations(input_data)
            else:
                analysis_result = self._perform_statistical_analysis(input_data)
            
            self.analysis_operations_performed_count += 1
            
            response_data = {
                'status': 'success',
                'analysis_type': analysis_type,
                'results': analysis_result,
                'metadata': {
                    'operations_count': self.analysis_operations_performed_count,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            return AgentMessage(
                sender_agent_name=self.agent_name,
                receiver_agent_names=[message.sender_agent_name],
                message_type=AgentMessageType.TASK_RESPONSE,
                payload=AgentMessagePayload(data_content=response_data),
                reply_to_message_id=message.message_id
            )
            
        except Exception as error:
            return self._create_error_response(message, str(error))
    
    def _perform_statistical_analysis(self, data: Any) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis"""
        if isinstance(data, list) and data and isinstance(data[0], (int, float)):
            return self._analyze_numeric_list(data)
        elif isinstance(data, dict):
            return self._analyze_dictionary(data)
        elif isinstance(data, list):
            return self._analyze_list_collection(data)
        
        return {'error': 'Unsupported data type for analysis'}
    
    def _analyze_numeric_list(self, numeric_data: List[float]) -> Dict[str, Any]:
        """Analyze list of numeric values"""
        if not numeric_data:
            return {'error': 'Empty dataset'}
        
        sorted_values = sorted(numeric_data)
        data_count = len(sorted_values)
        
        return {
            'analysis_type': 'numeric_statistics',
            'sample_size': data_count,
            'sum_total': sum(numeric_data),
            'mean_average': sum(numeric_data) / data_count,
            'median_middle': sorted_values[data_count // 2],
            'minimum_value': min(numeric_data),
            'maximum_value': max(numeric_data),
            'range_span': max(numeric_data) - min(numeric_data),
            'percentile_25': sorted_values[int(data_count * 0.25)],
            'percentile_75': sorted_values[int(data_count * 0.75)]
        }
    
    def _analyze_dictionary(self, data: Dict) -> Dict[str, Any]:
        """Analyze dictionary data structure"""
        numeric_fields = {
            key: value 
            for key, value in data.items() 
            if isinstance(value, (int, float))
        }
        
        string_fields = {
            key: value 
            for key, value in data.items() 
            if isinstance(value, str)
        }
        
        return {
            'analysis_type': 'dictionary_structure',
            'total_fields': len(data),
            'numeric_fields_count': len(numeric_fields),
            'string_fields_count': len(string_fields),
            'field_names': list(data.keys()),
            'numeric_fields_summary': {
                field: {'value': value, 'type': 'numeric'}
                for field, value in numeric_fields.items()
            }
        }
    
    def _analyze_list_collection(self, data: List) -> Dict[str, Any]:
        """Analyze list of mixed items"""
        numeric_items = [item for item in data if isinstance(item, (int, float))]
        dict_items = [item for item in data if isinstance(item, dict)]
        string_items = [item for item in data if isinstance(item, str)]
        
        analysis = {
            'analysis_type': 'list_collection',
            'total_items': len(data),
            'item_type_counts': {
                'numeric': len(numeric_items),
                'dictionary': len(dict_items),
                'string': len(string_items)
            }
        }
        
        if numeric_items:
            analysis['numeric_summary'] = self._analyze_numeric_list(numeric_items)
        
        return analysis
    
    def _detect_patterns_and_trends(self, data: Any) -> Dict[str, Any]:
        """Detect patterns and trends in data"""
        return {
            'analysis_type': 'pattern_recognition',
            'patterns_found': [],
            'trends': [],
            'anomalies': [],
            'note': 'Pattern detection requires time series or sequential data'
        }
    
    def _analyze_correlations(self, data: Any) -> Dict[str, Any]:
        """Analyze correlations between data fields"""
        return {
            'analysis_type': 'correlation_analysis',
            'correlations': [],
            'note': 'Correlation analysis requires multi-field datasets'
        }
    
    def _create_error_response(self, message: AgentMessage, error_message: str) -> AgentMessage:
        """Create error response message"""
        return AgentMessage(
            sender_agent_name=self.agent_name,
            receiver_agent_names=[message.sender_agent_name],
            message_type=AgentMessageType.ERROR_NOTIFICATION,
            payload=AgentMessagePayload(data_content={'error': error_message}),
            reply_to_message_id=message.message_id
        )


class ReportGenerationAgent(BaseAgent):
    """
    Specialized agent for generating reports and summaries.
    
    Capabilities:
      - report_generation: Create formatted reports
      - summary_generation: Generate executive summaries
      - format_conversion: Convert between formats (JSON, XML, CSV)
      - visualization_preparation: Prepare data for charts/graphs
    
    Example Use Cases:
      - Automated reporting
      - Dashboard data preparation
      - Export operations
      - Documentation generation
    """
    
    def __init__(self, agent_name: str = "report_generation_agent"):
        super().__init__(
            agent_name=agent_name,
            agent_description="Specialized agent for report generation and formatting",
            capability_list=[
                "report_generation",
                "summary_generation",
                "format_conversion",
                "visualization_preparation",
                "document_template_processing"
            ]
        )
        self.reports_generated_total_count = 0
    
    def process_task_request(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process report generation task request"""
        if message.payload is None:
            return self._create_error_response(message, "No payload provided")
        
        input_data = message.payload.data_content
        report_format = message.metadata.get('format', 'summary')
        
        try:
            if report_format == 'summary':
                report_content = self._generate_summary_report(input_data)
            elif report_format == 'detailed':
                report_content = self._generate_detailed_report(input_data)
            elif report_format == 'text':
                report_content = self._generate_text_report(input_data)
            elif report_format == 'structured':
                report_content = self._generate_structured_report(input_data)
            else:
                report_content = self._generate_summary_report(input_data)
            
            self.reports_generated_total_count += 1
            
            response_data = {
                'status': 'success',
                'report_format': report_format,
                'report': report_content,
                'generation_metadata': {
                    'reports_generated': self.reports_generated_total_count,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
            return AgentMessage(
                sender_agent_name=self.agent_name,
                receiver_agent_names=[message.sender_agent_name],
                message_type=AgentMessageType.TASK_RESPONSE,
                payload=AgentMessagePayload(data_content=response_data),
                reply_to_message_id=message.message_id
            )
            
        except Exception as error:
            return self._create_error_response(message, str(error))
    
    def _generate_summary_report(self, data: Any) -> Dict[str, Any]:
        """Generate summary report"""
        return {
            'report_type': 'summary',
            'title': f"Summary Report - {datetime.now().strftime('%Y-%m-%d')}",
            'data_overview': {
                'data_type': type(data).__name__,
                'size': len(data) if hasattr(data, '__len__') else 1,
                'structure': 'collection' if isinstance(data, (list, dict)) else 'scalar'
            },
            'generated_timestamp': datetime.now().isoformat()
        }
    
    def _generate_detailed_report(self, data: Any) -> Dict[str, Any]:
        """Generate detailed report with sections"""
        sections = []
        
        if isinstance(data, dict):
            sections.append({
                'section_title': 'Data Fields',
                'content': f"Contains {len(data)} fields: {', '.join(data.keys())}",
                'field_details': {
                    key: {'value': value, 'type': type(value).__name__}
                    for key, value in data.items()
                }
            })
        elif isinstance(data, list):
            sections.append({
                'section_title': 'Collection Summary',
                'content': f"Contains {len(data)} items",
                'sample_items': data[:5] if len(data) > 5 else data
            })
        
        sections.append({
            'section_title': 'Generation Information',
            'content': f"Report generated by {self.agent_name}",
            'metadata': {
                'generation_timestamp': datetime.now().isoformat(),
                'agent_name': self.agent_name
            }
        })
        
        return {
            'report_type': 'detailed',
            'title': f"Detailed Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            'sections': sections,
            'total_sections': len(sections)
        }
    
    def _generate_text_report(self, data: Any) -> str:
        """Generate human-readable text report"""
        lines = [
            "=" * 70,
            f"{self.agent_name.upper()} - ANALYSIS REPORT",
            "=" * 70,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-" * 70,
            ""
        ]
        
        if isinstance(data, dict):
            lines.append("DATA FIELDS:")
            for key, value in data.items():
                lines.append(f"  {key}: {value}")
        elif isinstance(data, list):
            lines.append(f"COLLECTION ({len(data)} items):")
            for index, item in enumerate(data[:5], 1):
                lines.append(f"  {index}. {item}")
            if len(data) > 5:
                lines.append(f"  ... and {len(data) - 5} more items")
        
        lines.extend(["", "=" * 70, "END OF REPORT", "=" * 70])
        return "\n".join(lines)
    
    def _generate_structured_report(self, data: Any) -> Dict[str, Any]:
        """Generate structured report with metadata"""
        return {
            'report_type': 'structured',
            'header': {
                'title': f"Structured Report - {datetime.now().strftime('%Y-%m-%d')}",
                'generated_at': datetime.now().isoformat(),
                'generator_agent': self.agent_name,
                'report_version': '1.0'
            },
            'body': {
                'data': data,
                'data_summary': {
                    'type': type(data).__name__,
                    'serializable': True
                }
            },
            'footer': {
                'report_id': str(uuid.uuid4()),
                'confidential': False
            }
        }
    
    def _create_error_response(self, message: AgentMessage, error_message: str) -> AgentMessage:
        """Create error response message"""
        return AgentMessage(
            sender_agent_name=self.agent_name,
            receiver_agent_names=[message.sender_agent_name],
            message_type=AgentMessageType.ERROR_NOTIFICATION,
            payload=AgentMessagePayload(data_content={'error': error_message}),
            reply_to_message_id=message.message_id
        )


import uuid
