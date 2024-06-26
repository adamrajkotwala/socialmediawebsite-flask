DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS like;
DROP TABLE IF EXISTS inbox;
DROP TABLE IF EXISTS relationship;
DROP TABLE IF EXISTS notification;
DROP TABLE IF EXISTS message;
DROP TABLE IF EXISTS conversation;

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
  content TEXT,
  time TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  post_id INTEGER,
  type TEXT NOT NULL,
  is_seen INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES user(id),
  FOREIGN KEY (other_user_id) REFERENCES user(id),
  FOREIGN KEY (post_id) REFERENCES post(id)
);

CREATE TABLE message (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id INTEGER NOT NULL,
  sender_id INTEGER NOT NULL,
  sender_username NOT NULL,
  sender_is_deleted NOT NULL DEFAULT 0,
  recipient_id INTEGER NOT NULL,
  recipient_username TEXT NOT NULL,
  recipient_is_deleted NOT NULL DEFAULT 0,
  content TEXT NOT NULL,
  time TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_read INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (sender_id) REFERENCES user(id),
  FOREIGN KEY (recipient_id) REFERENCES user(id)
  FOREIGN KEY (conversation_id) REFERENCES conversation(id)
);

CREATE TABLE conversation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_count INTEGER NOT NULL DEFAULT 0,
  first_last_message_id INTEGER,
  first_last_sender_id INTEGER,
  first_last_sender_username TEXT,
  first_last_message_preview TEXT,
  first_last_message_time TEXT,
  first_last_message_timestamp DATETIME,
  is_first_last_message_read INT NOT NULL DEFAULT 0,
  first_user_id INT NOT NULL,
  first_user_username TEXT NOT NULL,
  first_user_is_deleted NOT NULL DEFAULT 0,
  second_last_message_id INTEGER,
  second_last_sender_id INTEGER,
  second_last_sender_username TEXT,
  second_last_message_preview TEXT,
  second_last_message_time TEXT,
  second_last_message_timestamp DATETIME,
  is_second_last_message_read INT NOT NULL DEFAULT 0,
  second_user_id INT NOT NULL,
  second_user_username TEXT NOT NULL,
  second_user_is_deleted NOT NULL DEFAULT 0,
  FOREIGN KEY (first_user_id) REFERENCES user(id),
  FOREIGN KEY (second_user_id) REFERENCES user(id),
  UNIQUE (first_user_id, second_user_id)
);