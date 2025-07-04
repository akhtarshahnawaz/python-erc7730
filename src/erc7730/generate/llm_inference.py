import json
import os
from typing import Any

from openai import OpenAI

from erc7730.model.abi import Function
from erc7730.common.client import SourcifyContractData
from erc7730.model.display import FieldFormat, AddressNameType
from erc7730.model.input.display import InputFieldParameters, InputAddressNameParameters, InputTokenAmountParameters


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
            
            # Check if we got a valid response
            if not response.choices:
                print(f"Warning: No choices in LLM response for function {function.name or 'unknown'}")
                return {}
            
            result = response.choices[0].message.content
            if not result:
                print(f"Warning: Empty content in LLM response for function {function.name or 'unknown'}")
                return {}
            
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
            # Clean up the response - sometimes LLMs add markdown formatting
            cleaned_response = response.strip()
            
            # Remove markdown code blocks if present
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            # Check if response is empty
            if not cleaned_response:
                print("Warning: LLM returned empty response")
                return {}
            
            # Debug: print the response we're trying to parse (only when DEBUG env var is set)
            if os.environ.get("DEBUG") == "1":
                print(f"Debug: Attempting to parse LLM response: {cleaned_response[:200]}...")
            
            parsed = json.loads(cleaned_response)
            result = {}
            
            for param_name, format_info in parsed.items():
                format_name = format_info.get("format", "RAW")
                params = format_info.get("params")
                
                # Convert format string to enum - handle both camelCase and UPPER_CASE
                format_mapping = {
                    "RAW": FieldFormat.RAW,
                    "ADDRESS_NAME": FieldFormat.ADDRESS_NAME,
                    "CALL_DATA": FieldFormat.CALL_DATA,
                    "AMOUNT": FieldFormat.AMOUNT,
                    "TOKEN_AMOUNT": FieldFormat.TOKEN_AMOUNT,
                    "NFT_NAME": FieldFormat.NFT_NAME,
                    "DATE": FieldFormat.DATE,
                    "DURATION": FieldFormat.DURATION,
                    "UNIT": FieldFormat.UNIT,
                    "ENUM": FieldFormat.RAW,  # ENUM not in current FieldFormat, use RAW
                    # Also support camelCase versions
                    "raw": FieldFormat.RAW,
                    "addressName": FieldFormat.ADDRESS_NAME,
                    "calldata": FieldFormat.CALL_DATA,
                    "amount": FieldFormat.AMOUNT,
                    "tokenAmount": FieldFormat.TOKEN_AMOUNT,
                    "nftName": FieldFormat.NFT_NAME,
                    "date": FieldFormat.DATE,
                    "duration": FieldFormat.DURATION,
                    "unit": FieldFormat.UNIT,
                }
                
                field_format = format_mapping.get(format_name, FieldFormat.RAW)
                if format_name not in format_mapping:
                    print(f"Warning: Unknown format '{format_name}', using RAW")
                
                # Convert params to appropriate type based on format
                field_params = None
                if params and field_format != FieldFormat.RAW:
                    field_params = self._convert_params(field_format, params)
                
                result[param_name] = (field_format, field_params)
            
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse LLM response: {e}")
            print(f"Raw response was: {repr(response)}")
            return {}

    def _convert_params(self, field_format: FieldFormat, params: dict[str, Any]) -> InputFieldParameters | None:
        """Convert LLM-provided parameters to proper InputFieldParameters type."""
        try:
            match field_format:
                case FieldFormat.ADDRESS_NAME:
                    # Convert address types
                    types = params.get("types", [])
                    if isinstance(types, str):
                        types = [types]
                    
                    # Map LLM type names to AddressNameType enum values
                    type_mapping = {
                        "ACCOUNT": AddressNameType.EOA,
                        "EOA": AddressNameType.EOA,
                        "WALLET": AddressNameType.WALLET,
                        "CONTRACT": AddressNameType.CONTRACT,
                        "TOKEN": AddressNameType.TOKEN,
                        "COLLECTION": AddressNameType.COLLECTION,
                        # lowercase versions
                        "account": AddressNameType.EOA,
                        "eoa": AddressNameType.EOA,
                        "wallet": AddressNameType.WALLET,
                        "contract": AddressNameType.CONTRACT,
                        "token": AddressNameType.TOKEN,
                        "collection": AddressNameType.COLLECTION,
                    }
                    
                    converted_types = []
                    for type_name in types:
                        if type_name in type_mapping:
                            converted_types.append(type_mapping[type_name])
                        else:
                            print(f"Warning: Unknown address type '{type_name}', skipping")
                    
                    if converted_types:
                        return InputAddressNameParameters(types=converted_types)
                
                case FieldFormat.TOKEN_AMOUNT:
                    # For token amount, filter out unsupported parameters like 'decimals'
                    # InputTokenAmountParameters only accepts: tokenPath, token, nativeCurrencyAddress, threshold, message
                    supported_params = {}
                    for key, value in params.items():
                        if key in ["tokenPath", "token", "nativeCurrencyAddress", "threshold", "message"]:
                            supported_params[key] = value
                        elif key == "decimals":
                            # Skip decimals as it's derived from token metadata
                            continue
                        else:
                            print(f"Warning: Unsupported TOKEN_AMOUNT parameter '{key}', skipping")
                    
                    if supported_params:
                        return InputTokenAmountParameters(**supported_params)
                    else:
                        # Return None if no supported parameters, will use basic tokenAmount format
                        return None
                
                case _:
                    # For other formats, return the params as-is for now
                    return params
                    
        except Exception as e:
            print(f"Warning: Failed to convert parameters for {field_format}: {e}")
            return None
        
        return None