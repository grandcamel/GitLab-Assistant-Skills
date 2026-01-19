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
