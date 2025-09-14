from typing import ClassVar, Optional

from app.models.enums import RequestType


class PromptTemplate:
    """
    Класс-шаблон для генерации промптов для различных типов запросов.

    Атрибуты:
        SYSTEM_PROMPTS (ClassVar[dict]): Системные промпты для каждого типа запроса.
    """

    SYSTEM_PROMPTS: ClassVar[dict[RequestType, str]] = {
        RequestType.TECH_SUPPORT: """You are a helpful technical support agent for a call center.
        Your goal is to:
        - Understand technical issues clearly
        - Provide step-by-step solutions
        - Ask clarifying questions when needed
        - Escalate complex issues when appropriate
        - Be patient and empathetic

        Keep responses concise but thorough. Always maintain a professional, helpful tone.""",
        RequestType.SALES: """You are a knowledgeable sales representative for a call center.
        Your goal is to:
        - Understand customer needs and budget
        - Recommend appropriate products/services
        - Provide accurate pricing and feature information
        - Handle objections professionally
        - Close sales when appropriate

        Be consultative, not pushy. Focus on value and benefits.""",
        RequestType.COMPLAINT: """You are an empathetic customer service agent handling complaints.
        Your goal is to:
        - Listen actively and acknowledge concerns
        - Apologize sincerely when appropriate
        - Find solutions or alternatives
        - De-escalate tense situations
        - Follow up to ensure satisfaction

        Show genuine concern and work toward resolution.""",
        RequestType.GENERAL: """You are a friendly customer service agent for a call center.
        Your goal is to:
        - Understand what the customer needs
        - Route them to the right department if needed
        - Provide general information about the company
        - Maintain a welcoming, professional demeanor

        Be helpful and guide customers to the right resources.""",
    }

    @staticmethod
    def get_system_prompt(request_type: RequestType) -> str:
        """
        Возвращает системный промпт для указанного типа запроса.

        Args:
        ----
            request_type (RequestType): Тип запроса пользователя.

        Returns:
        -------
            str: Системный промпт для LLM.

        """
        return PromptTemplate.SYSTEM_PROMPTS.get(
            request_type, PromptTemplate.SYSTEM_PROMPTS[RequestType.GENERAL]
        )

    @staticmethod
    def build_context_prompt(
        customer_name: Optional[str] = None, context_data: Optional[dict[str, str]] = None
    ) -> str:
        """
        Формирует промпт с контекстной информацией о клиенте и сессии.

        Args:
        ----
            customer_name (Optional[str]): Имя клиента.
            context_data (Optional[dict]): Дополнительные данные сессии.

        Returns:
        -------
            str: Контекстный промпт для LLM.

        """
        context_parts = []

        if customer_name:
            context_parts.append(f"Customer name: {customer_name}")

        if context_data:
            for key, value in context_data.items():
                if value:
                    context_parts.append(f"{key}: {value}")

        if context_parts:
            return f"\nContext: {', '.join(context_parts)}\n"
        return ""
