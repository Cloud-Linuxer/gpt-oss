"""
Validation Tools

Provides data validation and format checking capabilities.
"""

import re
import ipaddress
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from datetime import datetime
from ..base import BaseTool, ToolResult, ToolError


class ValidationTool(BaseTool):
    """Data validation and format checking."""
    
    @property
    def name(self) -> str:
        return "validation"
    
    @property
    def description(self) -> str:
        return "Data validation: email, URL, IP, phone, credit card, format checking"
    
    @property
    def category(self) -> str:
        return "validation"
    
    @property
    def safety_level(self) -> str:
        return "safe"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "validation_type": {
                    "type": "string",
                    "enum": [
                        "email", "url", "ip_address", "phone", "credit_card",
                        "json", "xml", "date", "number", "uuid", "password_strength"
                    ],
                    "description": "검증할 데이터 유형"
                },
                "data": {
                    "type": "string",
                    "description": "검증할 데이터"
                },
                "options": {
                    "type": "object",
                    "description": "검증 옵션",
                    "properties": {
                        "strict": {"type": "boolean", "default": False},
                        "allow_international": {"type": "boolean", "default": True},
                        "min_length": {"type": "integer"},
                        "max_length": {"type": "integer"}
                    },
                    "additionalProperties": True
                }
            },
            "required": ["validation_type", "data"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        validation_type = kwargs.get("validation_type")
        data = kwargs.get("data", "")
        options = kwargs.get("options", {})
        
        try:
            if validation_type == "email":
                result = await self._validate_email(data, options)
            elif validation_type == "url":
                result = await self._validate_url(data, options)
            elif validation_type == "ip_address":
                result = await self._validate_ip_address(data, options)
            elif validation_type == "phone":
                result = await self._validate_phone(data, options)
            elif validation_type == "credit_card":
                result = await self._validate_credit_card(data, options)
            elif validation_type == "json":
                result = await self._validate_json(data, options)
            elif validation_type == "xml":
                result = await self._validate_xml(data, options)
            elif validation_type == "date":
                result = await self._validate_date(data, options)
            elif validation_type == "number":
                result = await self._validate_number(data, options)
            elif validation_type == "uuid":
                result = await self._validate_uuid(data, options)
            elif validation_type == "password_strength":
                result = await self._validate_password_strength(data, options)
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    message=f"Unknown validation type: {validation_type}"
                )
            
            return ToolResult(
                success=True,
                result=result,
                message=f"Validated {validation_type} data",
                metadata={"validation_type": validation_type, "data_length": len(str(data))}
            )
            
        except Exception as e:
            raise ToolError(f"Validation failed: {str(e)}", self.name)
    
    async def _validate_email(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate email address."""
        strict = options.get("strict", False)
        
        # Basic email regex
        if strict:
            # RFC 5322 compliant (simplified)
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        else:
            # More permissive
            pattern = r'^[^@]+@[^@]+\.[^@]+$'
        
        is_valid = bool(re.match(pattern, data))
        
        result = {
            "valid": is_valid,
            "email": data.lower() if is_valid else data,
        }
        
        if is_valid:
            local, domain = data.split('@')
            result.update({
                "local_part": local,
                "domain": domain.lower(),
                "length": len(data)
            })
        
        return result
    
    async def _validate_url(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate URL."""
        try:
            parsed = urlparse(data)
            
            # Basic validation
            is_valid = bool(parsed.scheme and parsed.netloc)
            
            if options.get("require_https", False):
                is_valid = is_valid and parsed.scheme == 'https'
            
            result = {
                "valid": is_valid,
                "url": data
            }
            
            if is_valid:
                result.update({
                    "scheme": parsed.scheme,
                    "domain": parsed.netloc,
                    "path": parsed.path,
                    "params": parsed.params,
                    "query": parsed.query,
                    "fragment": parsed.fragment
                })
            
            return result
            
        except Exception:
            return {"valid": False, "url": data}
    
    async def _validate_ip_address(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate IP address."""
        try:
            ip = ipaddress.ip_address(data)
            
            result = {
                "valid": True,
                "ip_address": str(ip),
                "version": ip.version,
                "is_private": ip.is_private,
                "is_global": ip.is_global,
                "is_loopback": ip.is_loopback,
                "is_multicast": ip.is_multicast
            }
            
            if ip.version == 4:
                result["is_reserved"] = ip.is_reserved
            
            return result
            
        except ValueError:
            return {"valid": False, "ip_address": data}
    
    async def _validate_phone(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate phone number."""
        # Remove common formatting characters
        cleaned = re.sub(r'[^\d+]', '', data)
        
        # Basic validation patterns
        patterns = [
            r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$',  # US/Canada
            r'^\+?[1-9]\d{1,14}$'  # International (E.164)
        ]
        
        is_valid = any(re.match(pattern, cleaned) for pattern in patterns)
        
        result = {
            "valid": is_valid,
            "original": data,
            "cleaned": cleaned,
            "length": len(cleaned)
        }
        
        if is_valid:
            result["formatted"] = self._format_phone(cleaned)
        
        return result
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number."""
        if phone.startswith('+1') or (phone.startswith('1') and len(phone) == 11):
            # US/Canada format
            digits = phone.lstrip('+1')
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        
        return phone
    
    async def _validate_credit_card(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate credit card number using Luhn algorithm."""
        # Remove spaces and dashes
        cleaned = re.sub(r'[^\d]', '', data)
        
        # Basic length check
        if len(cleaned) < 13 or len(cleaned) > 19:
            return {"valid": False, "number": data, "reason": "Invalid length"}
        
        # Luhn algorithm
        def luhn_check(card_num: str) -> bool:
            total = 0
            reverse_digits = card_num[::-1]
            
            for i, digit in enumerate(reverse_digits):
                n = int(digit)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n = n // 10 + n % 10
                total += n
            
            return total % 10 == 0
        
        is_valid = luhn_check(cleaned)
        
        # Determine card type
        card_type = self._get_card_type(cleaned)
        
        result = {
            "valid": is_valid,
            "original": data,
            "cleaned": cleaned,
            "masked": f"****-****-****-{cleaned[-4:]}",
            "length": len(cleaned),
            "card_type": card_type
        }
        
        return result
    
    def _get_card_type(self, number: str) -> str:
        """Determine credit card type."""
        if number.startswith('4'):
            return 'Visa'
        elif number.startswith(('51', '52', '53', '54', '55')):
            return 'MasterCard'
        elif number.startswith(('34', '37')):
            return 'American Express'
        elif number.startswith('6011') or number.startswith('65'):
            return 'Discover'
        else:
            return 'Unknown'
    
    async def _validate_json(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON format."""
        import json
        
        try:
            parsed = json.loads(data)
            return {
                "valid": True,
                "parsed": parsed,
                "type": type(parsed).__name__,
                "size": len(data)
            }
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": e.lineno,
                "column": e.colno
            }
    
    async def _validate_xml(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate XML format."""
        try:
            import xml.etree.ElementTree as ET
            ET.fromstring(data)
            return {
                "valid": True,
                "size": len(data)
            }
        except ET.ParseError as e:
            return {
                "valid": False,
                "error": str(e)
            }
        except ImportError:
            return {
                "valid": False,
                "error": "XML parsing not available"
            }
    
    async def _validate_date(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate date format."""
        format_str = options.get("format", "%Y-%m-%d")
        
        try:
            parsed_date = datetime.strptime(data, format_str)
            return {
                "valid": True,
                "date": data,
                "parsed": parsed_date.isoformat(),
                "year": parsed_date.year,
                "month": parsed_date.month,
                "day": parsed_date.day
            }
        except ValueError as e:
            return {
                "valid": False,
                "date": data,
                "error": str(e)
            }
    
    async def _validate_number(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate number format."""
        number_type = options.get("type", "any")  # int, float, any
        min_value = options.get("min_value")
        max_value = options.get("max_value")
        
        try:
            if number_type == "int":
                value = int(data)
            elif number_type == "float":
                value = float(data)
            else:
                # Try float first, then int
                try:
                    value = float(data)
                    if value.is_integer():
                        value = int(value)
                        detected_type = "int"
                    else:
                        detected_type = "float"
                except ValueError:
                    value = int(data)
                    detected_type = "int"
            
            # Range validation
            is_valid = True
            if min_value is not None and value < min_value:
                is_valid = False
            if max_value is not None and value > max_value:
                is_valid = False
            
            result = {
                "valid": is_valid,
                "value": value,
                "original": data,
                "type": detected_type if number_type == "any" else number_type
            }
            
            if not is_valid:
                result["reason"] = f"Value {value} outside range [{min_value}, {max_value}]"
            
            return result
            
        except ValueError as e:
            return {
                "valid": False,
                "original": data,
                "error": str(e)
            }
    
    async def _validate_uuid(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate UUID format."""
        import uuid
        
        try:
            parsed_uuid = uuid.UUID(data)
            return {
                "valid": True,
                "uuid": str(parsed_uuid),
                "version": parsed_uuid.version,
                "variant": parsed_uuid.variant.name if hasattr(parsed_uuid.variant, 'name') else str(parsed_uuid.variant)
            }
        except ValueError as e:
            return {
                "valid": False,
                "uuid": data,
                "error": str(e)
            }
    
    async def _validate_password_strength(self, data: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate password strength."""
        min_length = options.get("min_length", 8)
        require_uppercase = options.get("require_uppercase", True)
        require_lowercase = options.get("require_lowercase", True)
        require_digits = options.get("require_digits", True)
        require_special = options.get("require_special", True)
        
        score = 0
        feedback = []
        
        # Length check
        if len(data) >= min_length:
            score += 1
        else:
            feedback.append(f"Password must be at least {min_length} characters long")
        
        # Character type checks
        if require_uppercase and re.search(r'[A-Z]', data):
            score += 1
        elif require_uppercase:
            feedback.append("Password must contain at least one uppercase letter")
        
        if require_lowercase and re.search(r'[a-z]', data):
            score += 1
        elif require_lowercase:
            feedback.append("Password must contain at least one lowercase letter")
        
        if require_digits and re.search(r'\d', data):
            score += 1
        elif require_digits:
            feedback.append("Password must contain at least one digit")
        
        if require_special and re.search(r'[!@#$%^&*(),.?":{}|<>]', data):
            score += 1
        elif require_special:
            feedback.append("Password must contain at least one special character")
        
        # Additional scoring
        if len(data) >= 12:
            score += 1
        if len(set(data)) / len(data) > 0.7:  # Character diversity
            score += 1
        
        strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong"]
        strength = strength_levels[min(score, len(strength_levels) - 1)]
        
        return {
            "valid": score >= 4,
            "strength": strength,
            "score": score,
            "max_score": 6,
            "length": len(data),
            "feedback": feedback
        }