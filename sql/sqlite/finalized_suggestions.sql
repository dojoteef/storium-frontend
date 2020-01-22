SELECT
  uuid,
  json_extract(generated, '$.description') AS generated_text,
  json_extract(finalized, '$.description') AS user_text
FROM suggestion
WHERE cast(json_extract(finalized, '$.description') AS text) != 'null';
