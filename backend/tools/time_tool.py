"""시간대 도구 - 아시아/서울 기본, 다국 시간 지원"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from zoneinfo import ZoneInfo
import pytz
from .base import Tool, ToolResult, ToolStatus


class TimeTool(Tool):
    """시간대 정보를 제공하는 도구 (기본: 아시아/서울)"""
    
    def __init__(self):
        super().__init__(
            name="time_now",
            description="현재 시간을 다양한 시간대로 조회 (기본: 아시아/서울)"
        )
        
        # 주요 시간대 매핑
        self.timezone_aliases = {
            # 한국/아시아
            "한국": "Asia/Seoul",
            "서울": "Asia/Seoul", 
            "seoul": "Asia/Seoul",
            "korea": "Asia/Seoul",
            "도쿄": "Asia/Tokyo",
            "tokyo": "Asia/Tokyo",
            "일본": "Asia/Tokyo",
            "japan": "Asia/Tokyo",
            "베이징": "Asia/Shanghai", 
            "beijing": "Asia/Shanghai",
            "상하이": "Asia/Shanghai",
            "shanghai": "Asia/Shanghai",
            "중국": "Asia/Shanghai",
            "china": "Asia/Shanghai",
            "홍콩": "Asia/Hong_Kong",
            "hong kong": "Asia/Hong_Kong",
            "싱가포르": "Asia/Singapore",
            "singapore": "Asia/Singapore",
            
            # 미주
            "뉴욕": "America/New_York",
            "new york": "America/New_York",
            "미국동부": "America/New_York",
            "us east": "America/New_York",
            "로스앤젤레스": "America/Los_Angeles",
            "los angeles": "America/Los_Angeles",
            "la": "America/Los_Angeles",
            "라스베가스": "America/Los_Angeles",
            "vegas": "America/Los_Angeles",
            "las vegas": "America/Los_Angeles",
            "미국서부": "America/Los_Angeles",
            "us west": "America/Los_Angeles",
            "시카고": "America/Chicago",
            "chicago": "America/Chicago",
            "미국중부": "America/Chicago",
            "us central": "America/Chicago",
            
            # 유럽
            "런던": "Europe/London",
            "london": "Europe/London",
            "영국": "Europe/London",
            "uk": "Europe/London",
            "파리": "Europe/Paris",
            "paris": "Europe/Paris",
            "프랑스": "Europe/Paris",
            "france": "Europe/Paris",
            "베를린": "Europe/Berlin",
            "berlin": "Europe/Berlin",
            "독일": "Europe/Berlin",
            "germany": "Europe/Berlin",
            "모스크바": "Europe/Moscow",
            "moscow": "Europe/Moscow",
            "러시아": "Europe/Moscow",
            "russia": "Europe/Moscow",
            
            # 오세아니아
            "시드니": "Australia/Sydney",
            "sydney": "Australia/Sydney",
            "호주": "Australia/Sydney",
            "australia": "Australia/Sydney",
            
            # 특별 시간대
            "utc": "UTC",
            "gmt": "GMT",
        }
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "시간대 (기본: 서울). 예: '서울', '뉴욕', '런던', 'Asia/Seoul', 'UTC' 등",
                            "default": "서울"
                        },
                        "format": {
                            "type": "string",
                            "description": "출력 형식 선택",
                            "enum": ["standard", "detailed", "multiple"],
                            "default": "standard"
                        },
                        "zones": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "multiple 형식일 때 여러 시간대 목록 (예: ['서울', '뉴욕', '런던'])",
                            "default": []
                        }
                    }
                }
            }
        }
    
    def _normalize_timezone(self, timezone_input: str) -> str:
        """시간대 입력을 정규화"""
        if not timezone_input:
            return "Asia/Seoul"
            
        # 소문자로 변환하여 매칭 시도
        normalized = timezone_input.lower().strip()
        
        # 별칭 확인
        if normalized in self.timezone_aliases:
            return self.timezone_aliases[normalized]
            
        # 직접 시간대 이름인 경우 그대로 반환
        try:
            # 유효한 시간대인지 확인
            ZoneInfo(timezone_input)
            return timezone_input
        except:
            # 유효하지 않으면 기본값 반환
            return "Asia/Seoul"
    
    def _get_time_info(self, timezone_str: str) -> Dict[str, Any]:
        """특정 시간대의 시간 정보 조회"""
        try:
            tz = ZoneInfo(timezone_str)
            now = datetime.now(tz)
            
            return {
                "timezone": timezone_str,
                "timezone_name": timezone_str.split('/')[-1] if '/' in timezone_str else timezone_str,
                "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "iso_format": now.isoformat(),
                "timestamp": int(now.timestamp()),
                "weekday": now.strftime("%A"),
                "weekday_kr": self._get_korean_weekday(now.weekday()),
                "date_kr": now.strftime("%Y년 %m월 %d일"),
                "time_kr": now.strftime("%H시 %M분 %S초"),
                "utc_offset": now.strftime("%z"),
                "dst": now.dst() is not None and now.dst().total_seconds() != 0
            }
        except Exception as e:
            return {
                "timezone": timezone_str,
                "error": f"시간대 조회 실패: {str(e)}"
            }
    
    def _get_korean_weekday(self, weekday: int) -> str:
        """영어 요일을 한국어로 변환"""
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        return weekdays[weekday]
    
    async def execute(self, timezone: str = "서울", format: str = "standard", zones: List[str] = None) -> ToolResult:
        try:
            if format == "multiple" and zones:
                # 여러 시간대 조회
                results = []
                for zone in zones:
                    tz = self._normalize_timezone(zone)
                    time_info = self._get_time_info(tz)
                    results.append(time_info)
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "format": "multiple",
                        "timezones": results,
                        "total_zones": len(results)
                    }
                )
            
            else:
                # 단일 시간대 조회
                tz = self._normalize_timezone(timezone)
                time_info = self._get_time_info(tz)
                
                if "error" in time_info:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error=time_info["error"]
                    )
                
                if format == "detailed":
                    # 상세 정보 포함
                    time_info.update({
                        "available_aliases": [k for k, v in self.timezone_aliases.items() if v == tz],
                        "major_cities": self._get_major_cities(tz)
                    })
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=time_info
                )
                
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"시간 조회 중 오류: {str(e)}"
            )
    
    def _get_major_cities(self, timezone_str: str) -> List[str]:
        """해당 시간대의 주요 도시들"""
        city_mapping = {
            "Asia/Seoul": ["서울", "부산", "인천"],
            "Asia/Tokyo": ["도쿄", "오사카", "요코하마"],
            "Asia/Shanghai": ["베이징", "상하이", "광저우"],
            "America/New_York": ["뉴욕", "워싱턴DC", "보스턴"],
            "America/Los_Angeles": ["로스앤젤레스", "샌프란시스코", "라스베이거스"],
            "Europe/London": ["런던", "맨체스터", "에든버러"],
            "Europe/Paris": ["파리", "마르세유", "리옹"],
            "Europe/Berlin": ["베를린", "뮌헨", "함부르크"]
        }
        return city_mapping.get(timezone_str, [timezone_str.split('/')[-1]])


# 도구 인스턴스 생성 및 내보내기
time_tool = TimeTool()