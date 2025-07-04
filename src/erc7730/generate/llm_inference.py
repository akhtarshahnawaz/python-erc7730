import json
import os
from typing import Any

from openai import OpenAI

from erc7730.model.abi import Function
from erc7730.common.client import SourcifyContractData
from erc7730.model.display import FieldFormat
from erc7730.model.input.display import InputFieldParameters


class LLMInference:
    """LLM-based inference for generating ERC-7730 display formats."""

    def __init__(self) -> None:
        base_url = os.environ.get("OPENAI_BASE_URL")
        api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for --auto flag")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def infer_field_formats(
        self,
        function: Function,
        contract_data: SourcifyContractData | None = None,
    ) -> dict[str, tuple[FieldFormat, InputFieldParameters | None]]:
        """
        Use LLM to infer appropriate field formats for function parameters.
        
        :param function: ABI function to analyze
        :param contract_data: Optional contract data from Sourcify containing natspec
        :return: Dictionary mapping parameter names to format and parameters
        """
        # Filter out view/pure functions
        if function.stateMutability in ["view", "pure"]:
            return {}
        
        # Prepare context for LLM
        context = self._prepare_function_context(function, contract_data)
        
        # Generate prompt for LLM
        prompt = self._generate_prompt(context)
        
        try:
            response = self.client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(),
                    },
                    {
                        "role": "user", 
                        "content": prompt,
                    }
                ],
                temperature=0,
            )
            
            result = response.choices[0].message.content
            if result:
                return self._parse_llm_response(result)
            
        except Exception as e:
            print(f"Warning: LLM inference failed for function {function.name or 'unknown'}: {e}")
        
        return {}

    def _prepare_function_context(
        self, 
        function: Function, 
        contract_data: SourcifyContractData | None
    ) -> dict[str, Any]:
        """Prepare context information about the function for LLM analysis."""
        context = {
            "name": function.name or "",
            "inputs": [{"name": inp.name, "type": inp.type} for inp in function.inputs] if function.inputs else [],
            "state_mutability": function.stateMutability or "",
        }
        
        # Add natspec documentation if available
        if contract_data:
            if contract_data.userdoc and "methods" in contract_data.userdoc:
                function_sig = self._get_function_signature(function)
                if function_sig in contract_data.userdoc["methods"]:
                    context["userdoc"] = contract_data.userdoc["methods"][function_sig]
            
            if contract_data.devdoc and "methods" in contract_data.devdoc:
                function_sig = self._get_function_signature(function)
                if function_sig in contract_data.devdoc["methods"]:
                    context["devdoc"] = contract_data.devdoc["methods"][function_sig]
        
        return context

    def _get_function_signature(self, function: Function) -> str:
        """Generate function signature for natspec lookup."""
        name = function.name or ""
        inputs = function.inputs or []
        param_types = [param.type for param in inputs]
        return f"{name}({','.join(param_types)})"

    def _generate_prompt(self, context: dict[str, Any]) -> str:
        """Generate prompt for LLM based on function context."""
        prompt = f"""
Analyze this Ethereum smart contract function and suggest appropriate ERC-7730 display formats for each parameter.

Function: {context['name']}
State Mutability: {context['state_mutability']}

Parameters:
"""
        for param in context['inputs']:
            prompt += f"- {param.get('name', 'unknown')}: {param.get('type', 'unknown')}\n"
        
        if context.get('userdoc'):
            prompt += f"\nUser Documentation:\n{json.dumps(context['userdoc'], indent=2)}\n"
        
        if context.get('devdoc'):
            prompt += f"\nDeveloper Documentation:\n{json.dumps(context['devdoc'], indent=2)}\n"
        
        prompt += """
Based on the parameter names, types, and documentation, suggest the most appropriate ERC-7730 display format for each parameter.

Return ONLY a JSON object with parameter names as keys and format information as values.
Example format:
{
    "amount": {"format": "AMOUNT", "params": null},
    "token": {"format": "ADDRESS_NAME", "params": {"types": ["TOKEN"]}},
    "deadline": {"format": "DATE", "params": {"encoding": "TIMESTAMP"}}
}

Available formats: RAW, AMOUNT, TOKEN_AMOUNT, NFT_NAME, ADDRESS_NAME, CALL_DATA, DATE, DURATION, ENUM, UNIT
"""
        return prompt

    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM."""
        return """You are an expert in Ethereum smart contracts and ERC-7730 clear signing standards.

Your task is to analyze smart contract function parameters and suggest appropriate display formats that will help users understand what they are signing.

Key principles:
1. Choose formats that make transaction data human-readable
2. Consider parameter names, types, and documentation
3. Use ADDRESS_NAME for addresses that represent tokens, NFTs, or accounts
4. Use AMOUNT for numerical values representing quantities
5. Use DATE for timestamps and block heights
6. Use DURATION for time periods
7. Use TOKEN_AMOUNT for token quantities with decimals
8. Use CALL_DATA for encoded function calls
9. Use RAW as fallback for unclear cases

Always return valid JSON with the exact format requested."""

    def _parse_llm_response(self, response: str) -> dict[str, tuple[FieldFormat, InputFieldParameters | None]]:
        """Parse LLM response and convert to expected format."""
        try:
            parsed = json.loads(response.strip())
            result = {}
            
            for param_name, format_info in parsed.items():
                format_name = format_info.get("format", "RAW")
                params = format_info.get("params")
                
                # Convert format string to enum
                try:
                    field_format = FieldFormat(format_name)
                except ValueError:
                    field_format = FieldFormat.RAW
                
                # Convert params to appropriate type
                field_params = None
                if params:
                    # This would need more sophisticated parameter parsing
                    # based on the specific format type
                    field_params = params
                
                result[param_name] = (field_format, field_params)
            
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse LLM response: {e}")
            return {}