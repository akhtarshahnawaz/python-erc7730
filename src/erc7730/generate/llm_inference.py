import json
import os
from pathlib import Path
from typing import Any, NamedTuple

from openai import OpenAI

from erc7730.model.abi import Function
from erc7730.common.client import SourcifyContractData
from erc7730.model.display import FieldFormat, AddressNameType, DateEncoding
from erc7730.model.input.display import InputFieldParameters, InputAddressNameParameters, InputTokenAmountParameters, InputDateParameters


class FieldSuggestion(NamedTuple):
    """LLM suggestion for a field including format, parameters, and label."""
    format: FieldFormat
    params: InputFieldParameters | None
    label: str | None = None


class FunctionSuggestion(NamedTuple):
    """LLM suggestion for a function including fields and intent."""
    fields: dict[str, FieldSuggestion]
    intent: str | None = None


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
        
        # Cache LLM responses to avoid redundant API calls
        self._cache: dict[str, FunctionSuggestion] = {}
        
        # Load prompts from external files
        self._load_prompts()

    def infer_field_formats(
        self,
        function_data: Function,
        contract_data: SourcifyContractData | None = None,
    ) -> dict[str, tuple[FieldFormat, InputFieldParameters | None]]:
        """
        Use LLM to infer appropriate field formats for function parameters.
        
        :param function_data: ABI function to analyze
        :param contract_data: Optional contract data from Sourcify containing natspec
        :return: Dictionary mapping parameter names to format and parameters
        """
        # Filter out view/pure functions
        if function_data.stateMutability in ["view", "pure"]:
            return {}
        
        # Create cache key based on function signature
        function_sig = self._get_function_signature(function_data)
        
        # Check cache first
        if function_sig in self._cache:
            cached = self._cache[function_sig]
            return {name: (field.format, field.params) for name, field in cached.fields.items()}
        
        # Prepare context for LLM
        context = self._prepare_function_context(function_data, contract_data)
        
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
                print(f"Warning: No choices in LLM response for function {function_data.name or 'unknown'}")
                return {}
            
            result = response.choices[0].message.content
            if not result:
                print(f"Warning: Empty content in LLM response for function {function_data.name or 'unknown'}")
                return {}
            
            # Debug: print the raw LLM response
            if os.environ.get("DEBUG") == "1":
                print(f"Raw LLM response for {function_data.name}: {repr(result)}")
            
            function_suggestion = self._parse_llm_response(result, function_data)
            
            # Cache the results
            self._cache[function_sig] = function_suggestion
            
            # Return just the field formats for backward compatibility
            return {name: (field.format, field.params) for name, field in function_suggestion.fields.items()}
            
        except Exception as e:
            print(f"Warning: LLM inference failed for function {function_data.name or 'unknown'}: {e}")
            # Cache empty result to avoid retrying
            self._cache[function_sig] = FunctionSuggestion(fields={}, intent=None)
        
        return {}
    
    def get_field_label(self, function_data: Function, param_name: str) -> str | None:
        """Get LLM-suggested label for a specific field."""
        function_sig = self._get_function_signature(function_data)
        if function_sig in self._cache:
            cached = self._cache[function_sig]
            if param_name in cached.fields:
                return cached.fields[param_name].label
        return None
    
    def get_function_intent(self, function_data: Function) -> str | None:
        """Get LLM-suggested intent for a function."""
        function_sig = self._get_function_signature(function_data)
        if function_sig in self._cache:
            return self._cache[function_sig].intent
        return None

    def _prepare_function_context(
        self, 
        function_data: Function, 
        contract_data: SourcifyContractData | None
    ) -> dict[str, Any]:
        """Prepare context information about the function for LLM analysis."""
        context = {
            "name": function_data.name or "",
            "inputs": [{"name": inp.name, "type": inp.type} for inp in function_data.inputs] if function_data.inputs else [],
            "state_mutability": function_data.stateMutability or "",
        }
        
        # Add natspec documentation if available
        if contract_data:
            if contract_data.userdoc and "methods" in contract_data.userdoc:
                function_sig = self._get_function_signature(function_data)
                if function_sig in contract_data.userdoc["methods"]:
                    context["userdoc"] = contract_data.userdoc["methods"][function_sig]
            
            if contract_data.devdoc and "methods" in contract_data.devdoc:
                function_sig = self._get_function_signature(function_data)
                if function_sig in contract_data.devdoc["methods"]:
                    context["devdoc"] = contract_data.devdoc["methods"][function_sig]
        
        return context

    def _get_function_signature(self, function_data: Function) -> str:
        """Generate function signature for natspec lookup."""
        name = function_data.name or ""
        inputs = function_data.inputs or []
        param_types = [param.type for param in inputs]
        return f"{name}({','.join(param_types)})"

    def _generate_prompt(self, context: dict[str, Any]) -> str:
        """Generate prompt for LLM based on function context."""
        # Build parameters section
        parameters = ""
        for param in context['inputs']:
            parameters += f"- {param.get('name', 'unknown')}: {param.get('type', 'unknown')}\n"
        
        # Build documentation sections
        userdoc_section = ""
        if context.get('userdoc'):
            userdoc_section = f"\nUser Documentation:\n{json.dumps(context['userdoc'], indent=2)}\n"
        
        devdoc_section = ""
        if context.get('devdoc'):
            devdoc_section = f"\nDeveloper Documentation:\n{json.dumps(context['devdoc'], indent=2)}\n"
        
        # Format the template with actual values
        return self.user_prompt_template.format(
            function_name=context['name'],
            state_mutability=context['state_mutability'],
            parameters=parameters,
            userdoc_section=userdoc_section,
            devdoc_section=devdoc_section
        )
        return prompt

    def _load_prompts(self) -> None:
        """Load prompts from external text files."""
        # Get the directory containing this file
        current_dir = Path(__file__).parent
        # Navigate to the prompts directory
        prompts_dir = current_dir.parent.parent.parent / "prompts"
        
        # Load system prompt
        system_prompt_path = prompts_dir / "system_prompt.txt"
        if system_prompt_path.exists():
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
        else:
            raise FileNotFoundError(f"System prompt file not found: {system_prompt_path}")
        
        # Load user prompt template
        user_prompt_path = prompts_dir / "user_prompt_template.txt"
        if user_prompt_path.exists():
            with open(user_prompt_path, 'r', encoding='utf-8') as f:
                self.user_prompt_template = f.read()
        else:
            raise FileNotFoundError(f"User prompt template file not found: {user_prompt_path}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM."""
        return self.system_prompt

    def _parse_llm_response(self, response: str, function_data: Function) -> FunctionSuggestion:
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
                return FunctionSuggestion(fields={}, intent=None)
            
            # Log only when debug mode is enabled
            if os.environ.get("DEBUG") == "1":
                print(f"LLM Response for function {function_data.name or 'unknown'}:")
                print(f"Raw response: {repr(response)}")
                print(f"Cleaned response: {cleaned_response}")
                print("=" * 50)
            
            # Debug: print the response we're trying to parse (only when DEBUG env var is set)
            if os.environ.get("DEBUG") == "1":
                print(f"Debug: Attempting to parse LLM response: {cleaned_response[:200]}...")
            
            try:
                parsed = json.loads(cleaned_response)
            except json.JSONDecodeError as json_error:
                print(f"Warning: Failed to parse LLM response as JSON: {json_error}")
                print(f"Raw response: {repr(response)}")
                print(f"Cleaned response: {cleaned_response}")
                return FunctionSuggestion(fields={}, intent=None)
            
            # Extract intent
            intent = parsed.get("intent")
            
            # Extract fields
            fields_data = parsed.get("fields", {})
            fields = {}
            
            for param_name, field_info in fields_data.items():
                format_name = field_info.get("format", "RAW")
                params = field_info.get("params")
                label = field_info.get("label")
                
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
                
                fields[param_name] = FieldSuggestion(
                    format=field_format,
                    params=field_params,
                    label=label
                )
            
            return FunctionSuggestion(fields=fields, intent=intent)
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse LLM response: {e}")
            print(f"Raw response was: {repr(response)}")
            return FunctionSuggestion(fields={}, intent=None)

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
                
                case FieldFormat.DATE:
                    # Convert encoding string to DateEncoding enum
                    encoding = params.get("encoding")
                    if isinstance(encoding, str):
                        encoding_mapping = {
                            "timestamp": DateEncoding.TIMESTAMP,
                            "blockheight": DateEncoding.BLOCKHEIGHT,
                            "TIMESTAMP": DateEncoding.TIMESTAMP,
                            "BLOCKHEIGHT": DateEncoding.BLOCKHEIGHT,
                        }
                        enum_encoding = encoding_mapping.get(encoding)
                        if enum_encoding:
                            return InputDateParameters(encoding=enum_encoding)
                        else:
                            print(f"Warning: Unknown date encoding '{encoding}', using timestamp")
                            return InputDateParameters(encoding=DateEncoding.TIMESTAMP)
                    else:
                        # If encoding is not a string or missing, default to timestamp
                        return InputDateParameters(encoding=DateEncoding.TIMESTAMP)
                
                case _:
                    # For other formats, return None
                    return None
                    
        except Exception as e:
            print(f"Warning: Failed to convert parameters for {field_format}: {e}")
            return None
        
        return None