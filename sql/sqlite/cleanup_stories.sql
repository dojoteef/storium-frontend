CREATE TEMPORARY TABLE most_recent(game_pid, timestamp) AS
  (SELECT
    json_extract(s.story, '$.game_pid') AS game_pid,
    max(json_extract(s.story, '$.exported_at')) AS timestamp
  FROM story AS s
  GROUP BY json_extract(s.story, '$.game_pid'));
CREATE INDEX "most_recent_idx_temp_1" ON most_recent(game_pid);

DELETE FROM
  story
USING story AS s
  INNER JOIN  most_recent AS mr
  ON mr.game_pid = json_extract(s.story, '$.game_pid')
    LEFT OUTER JOIN suggestion AS sg
    ON sg.story_hash = s.hash
WHERE
  story.id = s.id
  AND sg.uuid IS NULL
  AND json_extract(s.story, '$.exported_at') < mr.timestamp;
