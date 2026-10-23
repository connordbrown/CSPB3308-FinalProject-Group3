CREATE TABLE `users` (
  `id` integer PRIMARY KEY,
  `first_name` text NOT NULL,
  `last_name` text NOT NULL,
  `email` text UNIQUE NOT NULL COLLATE NOCASE,
  `password_hash` text NOT NULL,
  `display_name` text UNIQUE,
  `created_at` timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE `companies` (
  `id` integer PRIMARY KEY, 
  `user_id` integer NOT NULL,
  `name` text NOT NULL COLLATE NOCASE,
  `city` text,
  `region` text,
  `website` text,
  `notes` text,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
);

CREATE TABLE `jobs` (
  `id` integer PRIMARY KEY, 
  `user_id` integer NOT NULL,
  `company_id` integer NOT NULL,
  `title` text NOT NULL,
  `link` text,
  `work_type` text 
    CHECK(work_type IN ( 'remote', 'hybrid', 'in person')),
  `notes` text,
  `status` text NOT NULL DEFAULT 'saved' 
    CHECK (status IN ('saved', 'applied', 'interviewing', 'offer', 'rejected', 'accepted', 'declined', 'withdrawn')),
  `date_applied` date,
  `created_at` timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`)
);

CREATE TABLE `contacts` (
  `id` integer PRIMARY KEY, 
  `user_id` integer NOT NULL,
  `company_id` integer,
  `job_id` integer,
  `name` text NOT NULL,
  `title` text,
  `designation` text
    CHECK (designation IN('recruiter', 'referrer', 'interviewer', 'hiring manager', 'other')),
  `email` text,
  `phone` text,
  `linkedin_url` text,
  `notes` text,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE SET NULL,
  FOREIGN KEY (`job_id`) REFERENCES `jobs` (`id`) ON DELETE SET NULL
);

CREATE UNIQUE INDEX `companies_index_0` ON `companies` (`user_id`, `name`);
