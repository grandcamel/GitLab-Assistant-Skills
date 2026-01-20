# Safeguards & Recovery Procedures

## Risk Level Matrix

| Risk | Symbol | Description | Safeguards |
|------|:------:|-------------|------------|
| Read-only | - | Safe operations, no confirmation | None |
| Caution | ⚠️ | Single-item modifications | Optional confirmation |
| Warning | ⚠️⚠️ | Bulk/destructive operations | Required confirmation, dry-run |
| Danger | ⚠️⚠️⚠️ | Irreversible operations | Double confirmation, backup |

## Pre-Operation Checklist

### Before Any Destructive Operation

1. [ ] Verify target (ID, name, filter)
2. [ ] Confirm scope (single vs. bulk)
3. [ ] Check permissions
4. [ ] Consider dry-run first
5. [ ] Note rollback procedure

### Before Bulk Operations

1. [ ] Run with `--dry-run` first
2. [ ] Review affected items
3. [ ] Confirm count is expected
4. [ ] Set reasonable batch size
5. [ ] Enable checkpointing for large batches

## Recovery Procedures

### Accidental Single Delete

1. Check if soft-delete is enabled
2. If yes, restore from trash within retention period
3. If no, restore from backup

### Accidental Bulk Modification

1. Stop immediately if in progress
2. Review checkpoint file for affected items
3. Reverse changes using bulk update
4. Or restore from backup

### Authentication Issues

1. Verify credentials: `glab auth status`
2. Re-authenticate: `glab auth login`
3. Check token expiration
4. Verify API endpoint connectivity

## Emergency Contacts

| Issue | Contact |
|-------|---------|
| API outage | Check GitLab status page |
| Security incident | Contact security team |
| Data loss | Contact backup administrator |

---

<!-- PERMISSIONS
permissions:
  cli: glab
  operations:
    # Safe - Read-only operations (list/view/status)
    - pattern: "glab mr list *"
      risk: safe
    - pattern: "glab mr view *"
      risk: safe
    - pattern: "glab mr status *"
      risk: safe
    - pattern: "glab mr diff *"
      risk: safe
    - pattern: "glab issue list *"
      risk: safe
    - pattern: "glab issue view *"
      risk: safe
    - pattern: "glab issue status *"
      risk: safe
    - pattern: "glab repo list *"
      risk: safe
    - pattern: "glab repo view *"
      risk: safe
    - pattern: "glab ci list *"
      risk: safe
    - pattern: "glab ci view *"
      risk: safe
    - pattern: "glab ci status *"
      risk: safe
    - pattern: "glab ci trace *"
      risk: safe
    - pattern: "glab release list *"
      risk: safe
    - pattern: "glab release view *"
      risk: safe
    - pattern: "glab auth status *"
      risk: safe
    - pattern: "glab project list *"
      risk: safe
    - pattern: "glab project view *"
      risk: safe
    - pattern: "glab label list *"
      risk: safe
    - pattern: "glab variable list *"
      risk: safe
    - pattern: "glab snippet list *"
      risk: safe
    - pattern: "glab snippet view *"
      risk: safe

    # Caution - Modifiable but easily reversible (create/approve/run)
    - pattern: "glab mr create *"
      risk: caution
    - pattern: "glab mr approve *"
      risk: caution
    - pattern: "glab mr revoke *"
      risk: caution
    - pattern: "glab mr update *"
      risk: caution
    - pattern: "glab mr note *"
      risk: caution
    - pattern: "glab mr rebase *"
      risk: caution
    - pattern: "glab issue create *"
      risk: caution
    - pattern: "glab issue update *"
      risk: caution
    - pattern: "glab issue note *"
      risk: caution
    - pattern: "glab issue reopen *"
      risk: caution
    - pattern: "glab issue close *"
      risk: caution
    - pattern: "glab ci run *"
      risk: caution
    - pattern: "glab ci retry *"
      risk: caution
    - pattern: "glab ci cancel *"
      risk: caution
    - pattern: "glab release create *"
      risk: caution
    - pattern: "glab release upload *"
      risk: caution
    - pattern: "glab label create *"
      risk: caution
    - pattern: "glab variable set *"
      risk: caution
    - pattern: "glab snippet create *"
      risk: caution
    - pattern: "glab repo fork *"
      risk: caution
    - pattern: "glab repo clone *"
      risk: caution

    # Warning - Destructive but potentially recoverable (merge/delete)
    - pattern: "glab mr merge *"
      risk: warning
    - pattern: "glab mr close *"
      risk: warning
    - pattern: "glab issue delete *"
      risk: warning
    - pattern: "glab release delete *"
      risk: warning
    - pattern: "glab label delete *"
      risk: warning
    - pattern: "glab variable delete *"
      risk: warning
    - pattern: "glab snippet delete *"
      risk: warning
    - pattern: "glab ci delete *"
      risk: warning

    # Danger - IRREVERSIBLE operations (repo delete)
    - pattern: "glab repo delete *"
      risk: danger
    - pattern: "glab project delete *"
      risk: danger
-->
