SELECT
  f.type,
  m.name AS model_name,
  round(avg(f.response::int), 2) AS avg_rating,
  round(stddev(f.response::int), 2) AS rating_stddev,
  count(m.name) AS feedback_count
FROM figmentator AS m
  INNER JOIN figmentator_for_story AS ffs
  ON m.id = ffs.model_id
    INNER JOIN suggestion AS s
    ON s.story_hash = ffs.story_hash
      INNER JOIN feedback AS f
      ON f.suggestion_id = s.uuid
WHERE
  array['fluency', 'likeability', 'relevance', 'coherence']::feedbacktype[] @> array[f.type]
  AND s.finalized::text != 'null'
  AND m.status != 'inactive'
GROUP BY f.type, m.name
ORDER BY f.type, avg_rating DESC;
