# ClearSignKit - AI-Powered ERC-7730 Generator

**Enhanced Python library for automated ERC-7730 clear signing schema generation**

This repository extends Ledger's official python-erc7730 library with AI-powered automation capabilities, making it easy to generate human-readable transaction schemas for any smart contract.

## 🚀 Key Features

### AI-Powered Schema Generation
- **OpenAI Integration**: Automatic schema generation using GPT models
- **Smart Analysis**: Analyzes function signatures, source code, and documentation
- **Custom Base URLs**: Support for OpenRouter and other AI providers
- **Sophisticated Prompting**: Context-aware prompts for accurate schema generation

### Decentralized Contract Data
- **Sourcify Integration**: Uses verified contracts from Sourcify's decentralized database
- **No API Keys Required**: Access to thousands of verified contracts without rate limits
- **Proxy Resolution**: Automatically detects and resolves proxy contracts
- **Rich Metadata**: Includes source code, documentation, and compilation artifacts

### Developer-Friendly Tools
- **Local Mode**: Process contracts from Hardhat deployment artifacts
- **CLI Interface**: Simple command-line interface for quick generation
- **Multiple Output Formats**: Support for various output destinations
- **Validation**: Built-in ERC-7730 schema validation

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/0xAkuti/python-erc7730.git
cd python-erc7730

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## ⚙️ Configuration

Create a `.env` file for AI functionality:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: use OpenRouter or other providers
OPENAI_MODEL=gpt-4o-mini  # Optional: default model
DEBUG=false  # Optional: enable debug logging
```

## 📖 Usage

### Basic Usage
```bash
# Generate schema for a contract
uv run python -m erc7730 generate \
  --chain-id 1 \
  --contract-address 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984 \
  --auto

# Generate from local Hardhat artifacts
uv run python -m erc7730 generate \
  --from-artifact ./artifacts/MyContract.sol/MyContract.json \
  --chain-id 1 \
  --contract-address 0x123... \
  --auto
```

### Advanced Options
```bash
# Specify output file
uv run python -m erc7730 generate \
  --chain-id 1 \
  --contract-address 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984 \
  --auto \
  --output-file ./schemas/uniswap.json

# Use custom AI model
OPENAI_MODEL=gpt-4 uv run python -m erc7730 generate \
  --chain-id 1 \
  --contract-address 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984 \
  --auto
```

## 🏗️ Architecture

This library serves as the core engine for the ClearSignKit ecosystem:

- **python-erc7730** (this repo): AI-powered schema generation engine
- **[clear-signing-erc7730-builder](https://github.com/0xAkuti/clear-signing-erc7730-builder)**: Web interface for visual schema building
- **[hardhat-clearsign](https://github.com/0xAkuti/hardhat-clearsign)**: Hardhat 3 plugin for development workflow integration

## 🤖 AI Integration

The `--auto` flag enables AI-powered schema generation:

1. **Contract Analysis**: Fetches contract ABI and source code from Sourcify
2. **Context Building**: Analyzes function signatures, parameters, and documentation
3. **AI Inference**: Uses OpenAI GPT models to generate human-readable descriptions
4. **Schema Generation**: Creates compliant ERC-7730 JSON schemas
5. **Validation**: Ensures generated schemas meet the standard requirements

## 🔗 Integration with ClearSignKit

This library integrates with:
- **Web Interface**: Called by the FastAPI backend in clear-signing-erc7730-builder
- **Hardhat Plugin**: Used by hardhat-clearsign for automated schema generation
- **Knowledge Graph**: Generated schemas can be published to The Graph's GRC-20 system

## 📚 Original Documentation

For the original ERC-7730 standard documentation, see: <https://ledgerhq.github.io/python-erc7730>

## 🤝 Contributing

This is a fork of Ledger's official python-erc7730 library with AI enhancements. Contributions are welcome!

## 📄 License

This project maintains the same license as the original Ledger library.
