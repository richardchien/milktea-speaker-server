from typing import Dict, Any, Optional


class Event(dict):
    @staticmethod
    def from_payload(payload: Dict[str, Any]) -> 'Optional[Event]':
        try:
            e = Event(payload)
            _ = e.type, e.detail_type
            return e
        except KeyError:
            return None

    @property
    def type(self) -> str:
        return self['type']

    @property
    def detail_type(self) -> str:
        return self['detail_type']

    @property
    def name(self):
        """
        事件名，即 ``{type}.{detail_type}``。
        """
        return f'{self.type}.{self.detail_type}'

    @property
    def self_id(self) -> Optional[str]:
        """智能音箱 ID。"""
        return self.get('self_id')

    @property
    def message_id(self) -> Optional[int]:
        """消息 ID。"""
        return self.get('message_id')

    @property
    def message(self) -> Any:
        """消息。"""
        return self.get('message')

    def __repr__(self) -> str:
        return f'<Event, {super().__repr__()}>'
