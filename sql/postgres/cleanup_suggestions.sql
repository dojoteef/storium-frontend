begin transaction;

delete from
  feedback as f
using suggestion as s
where
  f.suggestion_id = s.uuid
  and s.id >= 360 and s.id <= 435;

delete from
  suggestion
where id >= 360 and id <= 435;

rollback;
