DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS like;
DROP TABLE IF EXISTS inbox;
DROP TABLE IF EXISTS message;
DROP TABLE IF EXISTS relationship;
DROP TABLE IF EXISTS notification;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  birthday DATE,
  bio TEXT,
  profile_picture BLOB,
  friend_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TEXT,
  created_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_edited INTEGER NOT NULL DEFAULT 0,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  comment_count INTEGER NOT NULL DEFAULT 0,
  like_count INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE comment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  author_username TEXT NOT NULL,
  post_id INTEGER NOT NULL,
  created TEXT,
  created_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_edited INTEGER NOT NULL DEFAULT 0,
  body TEXT NOT NULL,
  comment_count INTEGER NOT NULL DEFAULT 0,
  like_count INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (author_id) REFERENCES user (id)
  FOREIGN KEY (author_username) REFERENCES user (username)
  FOREIGN KEY (post_id) REFERENCES post (id)
);

CREATE TABLE like (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user(id),
  FOREIGN KEY (post_id) REFERENCES post(id),
  UNIQUE (user_id, post_id)
);

CREATE TABLE inbox (
  user_id INTEGER NOT NULL,
  message_id INTEGER NOT NULL DEFAULT 0,
  is_deleted INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES user(id),
  FOREIGN KEY (message_id) REFERENCES message(id),
  UNIQUE (user_id, message_id)
);

CREATE TABLE message (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sender_id INTEGER NOT NULL,
  recipient_id INTEGER NOT NULL,
  content TEXT NOT NULL,
  time TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_read INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (sender_id) REFERENCES user(id),
  FOREIGN KEY (recipient_id) REFERENCES user(id)
);

CREATE TABLE relationship (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_user_id INTEGER NOT NULL,
  second_user_id INTEGER,
  status INTEGER DEFAULT 0,
  FOREIGN KEY (first_user_id) REFERENCES user(id),
  FOREIGN KEY (second_user_id) REFERENCES user(id),
  UNIQUE (first_user_id, second_user_id)
);

CREATE TABLE notification (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  other_user_id INTEGER,
  other_user_username TEXT,
  content TEXT NOT NULL,
  time TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  post_id INTEGER,
  type TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user(id),
  FOREIGN KEY (other_user_id) REFERENCES user(id),
  FOREIGN KEY (post_id) REFERENCES post(id),
  UNIQUE (user_id, other_user_id, post_id)
);
