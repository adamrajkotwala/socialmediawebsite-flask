INSERT INTO user (email, username, password, first_name, last_name, birthday, bio, profile_picture, friend_count)
VALUES
  ('example@gmail.com', 'test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 'John', 'Doe', '1990-01-01', 'This is a test bio', NULL, 0),
  ('other@gmail.com', 'other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79', 'Adam', 'Rajkotwala', '2003-01-21', 'Example bio', NULL, 0);

INSERT INTO post (title, body, author_id, created)
VALUES
  ('test title', 'test' || x'0a' || 'body', 1, '2018-01-01 00:00:00');