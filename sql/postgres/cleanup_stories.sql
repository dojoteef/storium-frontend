CREATE TEMPORARY TABLE most_recent(game_pid, timestamp) AS 
  (SELECT
    s.story->>'game_pid' AS game_pid,
    max(regexp_replace(s.story->>'exported_at', 'T', ' ')::timestamptz) AS timestamp
  FROM story AS s
  GROUP BY s.story->>'game_pid');
CREATE INDEX "most_recent_idx_temp_1" ON most_recent USING btree(game_pid);

DELETE FROM
  story
USING story AS s
  INNER JOIN  most_recent AS mr
  ON mr.game_pid = s.story->>'game_pid'
    LEFT OUTER JOIN suggestion AS sg
    ON sg.story_hash = s.hash
WHERE
  story.id = s.id
  AND sg.uuid IS NULL
  AND regexp_replace(s.story->>'exported_at', 'T', ' ')::timestamptz < mr.timestamp;
