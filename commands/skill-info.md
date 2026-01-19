---
description: "Get detailed information about a specific GitLab skill"
user_invocable: true
arguments:
  - name: skill_name
    description: "Name of the skill to get info about"
    required: true
---

# Skill Information

Get detailed information about a specific GitLab skill.

## Usage

```
/skill-info gitlab-issue
```

## Information Provided

- Skill description and purpose
- Available operations with risk levels
- CLI commands and options
- Common patterns and examples
- Related skills and documentation

## Example Output

For `gitlab-resource`:
- **Operations**: list, get, create, update, delete
- **Risk Level**: ⚠️ (modifiable)
- **Related**: gitlab-search, gitlab-bulk
