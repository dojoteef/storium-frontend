SELECT
  context.suggestion_id AS suggestion_id,
  context.model_name AS model_name,
  context.story AS story,
  context.generated AS generated,
  context.finalized AS finalized
FROM (
  SELECT
    sg.id AS suggestion_id,
    m.name AS model_name,
    s.story AS story,
    sg.generated AS generated,
    sg.finalized AS finalized,
    ROW_NUMBER() OVER (PARTITION BY m.name ORDER BY sg.id ASC) AS rno
  FROM figmentator AS m
    INNER JOIN figmentator_for_story AS ffs
    ON m.id = ffs.model_id

    INNER JOIN suggestion AS sg
    ON sg.story_hash = ffs.story_hash

    INNER JOIN story AS s
    ON sg.story_hash = s.hash
  WHERE
    sg.finalized::text != 'null'
    AND :status @> array[m.status]
    AND s.story->>'game_pid' != ALL(:blacklist)
  ORDER BY sg.id
) AS context
WHERE context.rno::FLOAT4 <= :limit
ORDER BY context.model_name;
