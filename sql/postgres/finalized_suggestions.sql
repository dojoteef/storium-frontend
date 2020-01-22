SELECT
  uuid,
  generated->>'description' AS generated_text,
  finalized->>'description' AS user_text
FROM suggestion
WHERE finalized::text != 'null';
