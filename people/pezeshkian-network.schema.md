# Schema — Pezeshkian Influence Network

## Person
- `person_id`: شناسه پایدار
- `name`: نام فرد
- `aliases`: نام‌های جایگزین

## Role Event
- `person_id`
- `role`
- `organization`
- `role_type`
- `start_at`
- `end_at`
- `status`
- `source_url`
- `source_published_at`
- `observed_at`
- `confidence`

## Influence Edge
- `from_person_id`
- `to_person_id`
- `relation_type`
- `domain`
- `weight`
- `valid_from`
- `valid_to`
- `evidence_id`
- `confidence`

## Event
- `event_id`
- `event_time`
- `observed_at`
- `event_type`
- `actors`
- `decision_target`
- `evidence_ids`

## Decision History
- `decision_id`
- `as_of`
- `input_evidence_ids`
- `network_snapshot_id`
- `prediction`
- `probability`
- `actual_outcome`
- `error_metric`

## ضد look-ahead bias
هر snapshot شبکه باید با `as_of` قابل بازسازی باشد. هیچ نقش، رابطه، خبر یا نتیجه‌ای که بعد از `as_of` منتشر/مشاهده شده نباید وارد ورودی پیش‌بینی تاریخی شود.
