# GitLab-Assistant-Skills

Claude Code Assistant Skills for GitLab.

## Quick Start

### 1. Install CLI

```bash
brew install glab
```

### 2. Authenticate

```bash
glab auth login
```

### 3. Load in Claude Code

```
/load gitlab
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `gitlab-assistant` | Hub skill for routing to specialized skills |

## Configuration

See [CLAUDE.md](CLAUDE.md) for configuration options and development guidelines.

## Development

### Run Tests

```bash
pytest skills/ -v
```

### Validate Project

```bash
python -m assistant_builder.validate_project .
```

## License

MIT License
