begin transaction;

delete from
  feedback as f
using suggestion as s
where
  f.suggestion_id = s.uuid
  and s.id >= 360 and s.id <= 384;

delete from
  suggestion
where id >= 360 and id <= 384;

rollback;
