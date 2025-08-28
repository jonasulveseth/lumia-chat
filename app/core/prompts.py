"""
Prompt templates and instructions for Lumia LLM.
"""
from typing import Dict, Any
from datetime import datetime
from app.core.config import settings


class PromptTemplates:
    """Templates for different types of prompts."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the main system prompt."""
        return settings.system_prompt
    
    @staticmethod
    def get_chat_prompt(user_message: str, context: str = None) -> str:
        """Get formatted chat prompt."""
        system_prompt = PromptTemplates.get_system_prompt()
        # Inject current date to help the LLM reason about "idag/igår" correctly
        today_str = datetime.now().strftime("%Y-%m-%d")
        system_prompt = f"{system_prompt}\n\nDagens datum: {today_str}\n\nInstruktion om metadata: Om context innehåller metadata-fält (t.ex. content_type), ta särskild hänsyn till detta.\n- Prioritera content_type=chat för dialogsammanhang och användartoner.\n- När användaren refererar till en fil, eller context antyder content_type=file, behandla detta som filinnehåll: beskriv, sammanfatta eller hämta relevanta delar från filen.\n- Om flera content_types finns, vikta chat högt för samtalston men låt file styra faktainnehåll när frågan gäller dokument/filer."
        
        if context:
            return f"{system_prompt}\n\nContext: {context}\n\nUser: {user_message}\nLumia:"
        else:
            return f"{system_prompt}\n\nUser: {user_message}\nLumia:"
    
    @staticmethod
    def get_code_generation_prompt(description: str, language: str = "python") -> str:
        """Get prompt for code generation."""
        return f"""{settings.system_prompt}

Du är en expert på {language}-programmering. Generera kod baserat på följande beskrivning:

Beskrivning: {description}

Språk: {language}

Kod:"""
    
    @staticmethod
    def get_analysis_prompt(topic: str, data: str = None) -> str:
        """Get prompt for analysis tasks."""
        base_prompt = f"""{settings.system_prompt}

Du ska analysera följande ämne: {topic}

"""
        if data:
            base_prompt += f"Data att analysera:\n{data}\n\n"
        
        base_prompt += "Analys:"
        return base_prompt
    
    @staticmethod
    def get_creative_prompt(creative_task: str) -> str:
        """Get prompt for creative tasks."""
        return f"""{settings.system_prompt}

Du ska vara kreativ och fantasifull. Uppgift: {creative_task}

Svar:"""


class PromptInstructions:
    """Instructions for different conversation types."""
    
    @staticmethod
    def get_instruction_for_topic(topic: str) -> str:
        """Get specific instruction based on conversation topic."""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['kod', 'programmering', 'python', 'javascript']):
            return "Använd kodblock och förklara steg för steg."
        
        elif any(word in topic_lower for word in ['analys', 'data', 'statistik']):
            return "Strukturera svaret med rubriker och listor."
        
        elif any(word in topic_lower for word in ['kreativ', 'idé', 'brainstorm']):
            return "Var fantasifull och använd bullet points."
        
        elif any(word in topic_lower for word in ['plan', 'strategi', 'projekt']):
            return "Skapa en strukturerad plan med numrerade steg."
        
        else:
            return "Använd Markdown-formatering för läsbarhet."
    
    @staticmethod
    def enhance_prompt_with_instruction(base_prompt: str, instruction: str) -> str:
        """Add specific instruction to base prompt."""
        return f"{base_prompt}\n\nNote: {instruction}" 