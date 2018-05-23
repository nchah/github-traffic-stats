-- These tables are an alternative to the CSV files being created

DROP TABLE IF EXISTS repo_overview;
DROP TABLE IF EXISTS repo_visitors; 
DROP TABLE IF EXISTS repo_clones;
DROP TABLE IF EXISTS repo_referrals; 

CREATE TABLE repo_overview(
   create_timestamp DATE         NOT NULL DEFAULT DATE(NOW()), -- date of generated results
   Repo_Name        VARCHAR(255) NOT NULL DEFAULT '', 
   Result_Type      VARCHAR(255) NOT NULL DEFAULT '', 
   Uniques          INT          NOT NULL DEFAULT 0,
   Total            INT          NOT NULL DEFAULT 0 
); 

CREATE TABLE repo_visitors( 
   Repo_Name        VARCHAR(255) NOT NULL DEFAULT '',
   create_timestamp DATE         NOT NULL DEFAULT DATE(NOW()), 
   Uniques          INT          NOT NULL DEFAULT 0, 
   Total            INT          NOT NULL DEFAULT 0
); 


CREATE table repo_clones( 
   Repo_Name        VARCHAR(255) NOT NULL DEFAULT '', 
   create_timestamp DATE         NOT NULL DEFAULT DATE(NOW()), 
   Uniques          INT          NOT NULL DEFAULT 0, 
   Total            INT          NOT NULL DEFAULT 0
); 

CREATE TABLE repo_referrals(
   Repo_Name        VARCHAR(255) NOT NULL DEFAULT '',
   Referral         VARCHAR(255) NOT NULL DEFAULT '',
   Uniques          INT          NOT NULL DEFAULT 0,
   Total            INT          NOT NULL DEFAULT 0
);  

