-- MySQL dump 10.13  Distrib 8.0.31, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: snow_plume
-- ------------------------------------------------------
-- Server version	8.0.31

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping routines for database 'snow_plume'
--
/*!50003 DROP PROCEDURE IF EXISTS `ero_log_blockupdate` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_log_blockupdate`(
artwork_id INT,
is_blocked boolean
)
BEGIN
	UPDATE ero_meta em
    SET em.is_blocked = is_blocked
    WHERE em.artwork_id = artwork_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_log_insert` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_log_insert`(
user_id CHAR(12),
group_id CHAR(12),
OUT times_of_ero TINYINT UNSIGNED
)
BEGIN	
    -- 检查是否是当天首次
    SET times_of_ero = (SELECT count(*) FROM 
			(SELECT DATE_FORMAT(datetime,'%Y-%m-%d') AS date1 FROM ero_log AS e WHERE e.user_id=user_id AND e.group_id=group_id) as subquery
            WHERE subquery.date1 = date(now()));
    
    -- 插入数据
	INSERT INTO ero_log()
    VALUES(
    user_id,
    group_id,
    now()
    );

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_log_query` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_log_query`(
user_id CHAR(12),
group_id CHAR(12),
OUT times_of_ero TINYINT UNSIGNED
)
BEGIN	
    -- 获取该用户当天涩涩的次数
    SET times_of_ero = (SELECT count(*) FROM 
			(SELECT DATE_FORMAT(datetime,'%Y-%m-%d') AS date1 FROM ero_log AS e WHERE e.user_id=user_id AND e.group_id=group_id) as subquery
            WHERE subquery.date1 = date(now()));


END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_log_update` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_log_update`(
artwork_id INT,
user_id CHAR(12),
group_id CHAR(12)
)
BEGIN
	-- 写入get_log
INSERT INTO ero_log ()
VALUES(
	user_id,
	group_id,
	now(),
	artwork_id
);

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_meta_fetch` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_meta_fetch`(
artwork_id INT,
OUT title VARCHAR(255),
OUT description VARCHAR(1024),
OUT user_id VARCHAR(45),
OUT user_name varchar(45),
OUT upload_date DATE,
OUT update_from_upload MEDIUMINT,
OUT url_p0 varchar(128),
OUT page_count char(3),
OUT like_count varchar(8),
OUT bookmark_count varchar(8),
OUT comment_count varchar(8),
OUT view_count varchar(8),
OUT is_original boolean,
OUT is_ai boolean,
OUT is_r18 boolean,
OUT is_blocked boolean,
OUT is_delete boolean
)
BEGIN
SET title = (SELECT e.title From ero_meta e WHERE e.artwork_id = artwork_id);
SET description = (SELECT e.description From ero_meta e WHERE e.artwork_id = artwork_id);
SET user_id = (SELECT e.user_id From ero_meta e WHERE e.artwork_id = artwork_id);
SET user_name = (SELECT e.user_name From ero_meta e WHERE e.artwork_id = artwork_id);
SET upload_date = (SELECT e.upload_date From ero_meta e WHERE e.artwork_id = artwork_id);
SET update_from_upload = (SELECT e.update_from_upload From ero_meta e WHERE e.artwork_id = artwork_id);
SET url_p0 = (SELECT e.url_p0 From ero_meta e WHERE e.artwork_id = artwork_id);
SET page_count = (SELECT e.page_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET like_count = (SELECT e.like_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET bookmark_count = (SELECT e.bookmark_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET comment_count = (SELECT e.comment_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET view_count = (SELECT e.view_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET is_original = (SELECT e.is_original From ero_meta e WHERE e.artwork_id = artwork_id);
SET is_ai = (SELECT e.is_ai From ero_meta e WHERE e.artwork_id = artwork_id);
SET is_r18 = (SELECT e.is_r18 From ero_meta e WHERE e.artwork_id = artwork_id);
SET is_blocked = (SELECT e.is_blocked From ero_meta e WHERE e.artwork_id = artwork_id);
SET is_delete = (SELECT e.is_delete From ero_meta e WHERE e.artwork_id = artwork_id);


END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_meta_insert` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_meta_insert`(
artwork_id INT,
title VARCHAR(255),
description VARCHAR(1024),
user_id VARCHAR(45),
user_name varchar(45),
upload_date DATE,
update_from_upload MEDIUMINT,
url_p0 varchar(128),
page_count char(3),
like_count varchar(8),
bookmark_count varchar(8),
comment_count varchar(8),
view_count varchar(8),
is_original boolean,
is_ai boolean,
is_r18 boolean
)
BEGIN
-- 插入除tag以外的元数据
Insert into ero_meta()
VALUES(
artwork_id,
title,
description,
user_id,
user_name,
upload_date,
update_from_upload,
url_p0,
page_count,
like_count,
bookmark_count,
comment_count,
view_count,
is_original,
is_ai,
is_r18,
null,
false
);


END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_meta_query` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_meta_query`(
artwork_id INT,
OUT title VARCHAR(255),
OUT description VARCHAR(1024),
OUT user_id VARCHAR(45),
OUT user_name varchar(45),
OUT upload_date DATE,
OUT update_from_upload MEDIUMINT,
OUT url_p0 varchar(128),
OUT page_count char(3),
OUT like_count varchar(8),
OUT bookmark_count varchar(8),
OUT comment_count varchar(8),
OUT view_count varchar(8),
OUT is_original boolean,
OUT is_ai boolean,
OUT is_r18 boolean,
OUT is_blocked boolean
)
BEGIN
SET title = (SELECT e.title From ero_meta e WHERE e.artwork_id = artwork_id);
SET description = (SELECT e.description From ero_meta e WHERE e.artwork_id = artwork_id);
SET user_id = (SELECT e.user_id From ero_meta e WHERE e.artwork_id = artwork_id);
SET user_name = (SELECT e.user_name From ero_meta e WHERE e.artwork_id = artwork_id);
SET upload_date = (SELECT e.upload_date From ero_meta e WHERE e.artwork_id = artwork_id);
SET update_from_upload = (SELECT e.update_from_upload From ero_meta e WHERE e.artwork_id = artwork_id);
SET url_p0 = (SELECT e.url_p0 From ero_meta e WHERE e.artwork_id = artwork_id);
SET page_count = (SELECT e.page_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET like_count = (SELECT e.like_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET bookmark_count = (SELECT e.bookmark_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET comment_count = (SELECT e.comment_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET view_count = (SELECT e.view_count From ero_meta e WHERE e.artwork_id = artwork_id);
SET is_original = (SELECT e.is_original From ero_meta e WHERE e.artwork_id = artwork_id);
SET is_ai = (SELECT e.is_ai From ero_meta e WHERE e.artwork_id = artwork_id);
SET is_r18 = (SELECT e.is_r18 From ero_meta e WHERE e.artwork_id = artwork_id);
SET is_blocked = (SELECT e.last_get_time From ero_meta e WHERE e.artwork_id = artwork_id);


END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_meta_update` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_meta_update`(
artwork_id INT,
title VARCHAR(255),
description VARCHAR(1024),
user_name VARCHAR(45),
like_count varchar(8),
bookmark_count varchar(8),
comment_count varchar(8),
view_count varchar(8),
update_from_upload MEDIUMINT,
is_delete boolean
)
BEGIN

-- 更新热度信息
UPDATE ero_meta e
SET e.title = title,
	e.description = description,
	e.user_name = user_name,
    e.like_count = like_count,
	e.bookmark_count = bookmark_count,
    e.comment_count = comment_count,
    e.view_count = view_count,
    e.update_from_upload = update_from_upload,
    e.is_delete = is_delete
WHERE e.artwork_id = artwork_id;





END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_tag_children_insert` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_tag_children_insert`(
tag varchar(63),
children_tag varchar(63)
)
BEGIN
DECLARE foo boolean;
DECLARE dup boolean DEFAULT false;
DECLARE CONTINUE HANDLER FOR 1062 SET dup=True;

-- 先检查children_tag是否存在，不存在则在ero_tags表里先插入
if not exists (select * from ero_tags where tag_name = children_tag) then
	insert into ero_tags()
	values(
	default,
	children_tag,
	'',
	null,
	null
	);
else
	SET foo = true;	-- 什么也不做
end if;

-- 再写入ero_tags_children表
INSERT INTO ero_tags_children()
VALUES(
(SELECT e.tag_id from ero_tags e where e.tag_name = tag limit 1),
(SELECT e.tag_id from ero_tags e where e.tag_name = children_tag limit 1)
);




END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_tag_info_insert` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_tag_info_insert`(
tag varchar(63),
translation varchar(63),
description varchar(512),
parent_tag varchar(63)
)
BEGIN
DECLARE foo boolean;

if translation = '' then
	SET translation = null;
end if;
if description = '' then
	set description = null;
end if;
if parent_tag = '' then
	SET parent_tag = null;
end if;


-- 先检查parent_tag是否存在，不存在则在ero_tags表里先插入
if not exists (select * from ero_tags where tag_name = parent_tag) then
	if parent_tag is null then
		SET foo = True;
	else
		insert into ero_tags()
		values(
		default,
		parent_tag,
		'',
		null,
		null
		);
	end if;
else
	SET foo = True;	-- 什么也不做
end if;


-- 如果数据存在就更新，不存在则新建
replace into ero_tags()
values(default,tag,translation,description,
	(SELECT tag_id from (SELECT tag_id from ero_tags where tag_name = parent_tag limit 1) temp));
    
-- 在进行更新和删除操作的时候，条件语句里面有涉及该数据的子查询语句，会报1093错误，通过嵌套子查询语句建立临时表来避免





END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_tag_insert_from_meta` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_tag_insert_from_meta`(
artwork_id INT,
tag_name VARCHAR(63),
tag_name_trans VARCHAR(63)
)
BEGIN
-- 检查tag是否已存在，若不存在，则在tag表里新建tag
DECLARE dup boolean DEFAULT false;
DECLARE CONTINUE HANDLER FOR 1062 SET dup=True;


if tag_name_trans is null then
	INSERT INTO ero_tags()
	values(
	DEFAULT,
	tag_name,
	'',	-- 要将null转为空字符串储存，否则联合唯一索引会失效（另外，判断一个值为null时要用 is null，不能用 = null）
    null,
    null
	);
else
	INSERT INTO ero_tags()
	values(
	DEFAULT,
	tag_name,
	tag_name_trans,
    null,
    null
	);
end if;

-- 在meta-tag链接表里插入tag数据

if tag_name_trans is null then
	INSERT INTO ero_meta_tag()
	values(
	artwork_id,
	(SELECT tag_id From ero_tags e WHERE (e.tag_name = tag_name and e.tag_name_trans = '') limit 1)	
	);
else
	INSERT INTO ero_meta_tag()
	values(
	artwork_id,
	(SELECT tag_id From ero_tags e WHERE (e.tag_name = tag_name and e.tag_name_trans = tag_name_trans) limit 1)
	);
end if;



END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ero_tag_siblings_insert` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ero_tag_siblings_insert`(
tag varchar(63),
siblings_tag varchar(63)
)
BEGIN
DECLARE foo boolean;
DECLARE dup boolean DEFAULT false;
DECLARE CONTINUE HANDLER FOR 1062 SET dup=True;

-- 先检查siblings_tag是否存在，不存在则在ero_tags表里先插入
if not exists (select * from ero_tags where tag_name = siblings_tag) then
	insert into ero_tags()
	values(
	default,
	siblings_tag,
	'',
	null,
	null
	);
else
	SET foo = True;	-- 什么也不做
end if;

-- 再写入ero_tags_siblings表
INSERT INTO ero_tags_siblings()
VALUES(
(SELECT e.tag_id from ero_tags e where e.tag_name = tag limit 1),
(SELECT e.tag_id from ero_tags e where e.tag_name = siblings_tag limit 1)
);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `fortune_get` */;
ALTER DATABASE `snow_plume` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `fortune_get`(
	user_id CHAR(12),
    OUT fortune SMALLINT,
	OUT level_name CHAR(2),
    OUT greetings VARCHAR(45),
    OUT greeting_content VARCHAR(45),
    OUT charm_item VARCHAR(20),
    OUT charm_content VARCHAR(45)
)
BEGIN
	DECLARE fortune_value_var,k,level_var,greetings_var,charm_var,a SMALLINT;
    -- 初始化fortune_value
    SET fortune_value_var = floor(rand()*114-3);
    -- 找到fortune_value对应的时运等级，返回level_var（即level_id）
    SET k = 0;
    REPEAT
        SET k = k + 1;
	UNTIL 
		fortune_value_var >= (
			 SELECT value_min FROM fortune_levels
			 WHERE level_id = k-1) 
		AND
        fortune_value_var <= (
			 SELECT value_max FROM fortune_levels
			 WHERE level_id = k-1) 
	END REPEAT;
    SET level_var = (SELECT level_id FROM fortune_levels WHERE level_id = k-1);
	
    -- 根据level_var，抽取对应level的greetings和幸运物
    SET a = floor(rand()*(SELECT COUNT(greetings_fortune_id) FROM fortune_greetings WHERE level_id = level_var));
    SET greetings_var = 
		(SELECT greetings_fortune_id FROM fortune_greetings WHERE level_id = level_var LIMIT 
			a,1);
    
    SET charm_var = floor(rand()*(SELECT COUNT(luck_charm_id) FROM fortune_charms)+1);
    
    -- 将抽签结果写入数据库
	INSERT INTO fortune_get(
			date,
            user_id,
            fortune_value,
            level_id,
            greetings_fortune_id,
            luck_charm_id)
	VALUES(
		DATE(now()),
        user_id,
        fortune_value_var,
        level_var,
        greetings_var,
        charm_var
		);
        
	-- 准备输出
    SET fortune = fortune_value_var,
	    level_name = (SELECT name From fortune_levels WHERE level_id = level_var),
        greetings = (SELECT f.greeting_content FROM fortune_levels AS f WHERE level_id = level_var),
        greeting_content = (SELECT content FROM fortune_greetings WHERE greetings_fortune_id = greetings_var),
        charm_item = (SELECT item From fortune_charms WHERE luck_charm_id = charm_var),
        charm_content = (SELECT content From fortune_charms WHERE luck_charm_id = charm_var);
    
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `snow_plume` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
/*!50003 DROP PROCEDURE IF EXISTS `fortune_get_when_duplicated` */;
ALTER DATABASE `snow_plume` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `fortune_get_when_duplicated`(
	user_id CHAR(12),
    OUT fortune SMALLINT,
	OUT level_name CHAR(2),
    OUT greetings VARCHAR(45),
    OUT greeting_content VARCHAR(45),
    OUT charm_item VARCHAR(20),
    OUT charm_content VARCHAR(45)
	)
BEGIN
	-- 同一user_id在某一天多次请求今日运势时，直接返回已有值
	DECLARE today DATE;
    SET today = DATE(now());
    SET fortune = (
			SELECT fortune_value 
            FROM fortune_get AS g 
            WHERE g.date = today AND g.user_id = user_id),
	    level_name = (
			SELECT name 
			From fortune_levels
			JOIN fortune_get AS g 
			USING (level_id)
			WHERE g.date = today AND g.user_id = user_id),
        greetings = (
			SELECT f.greeting_content 
            FROM fortune_levels AS f
            JOIN fortune_get AS g
            USING (level_id)
            WHERE g.date = today AND g.user_id = user_id),
        greeting_content = (
			SELECT content 
            FROM fortune_greetings 
            JOIN fortune_get AS g
            USING (greetings_fortune_id)
            WHERE g.date = today AND g.user_id = user_id),
        charm_item = (
			SELECT item 
            From fortune_charms
            JOIN fortune_get AS g
            USING (luck_charm_id)
            WHERE g.date = today AND g.user_id = user_id),
        charm_content = (
			SELECT content 
            From fortune_charms
            JOIN fortune_get AS g
            USING (luck_charm_id)
            WHERE g.date = today AND g.user_id = user_id);

END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `snow_plume` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
/*!50003 DROP PROCEDURE IF EXISTS `pixiv_crawler_query` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `pixiv_crawler_query`(
tag varchar(63),
OUT artwork_count mediumint
)
BEGIN

-- 如果表中有数据，那么返回该tag的作品数量
if exists (SELECT p.artwork_count from pixiv_crawler_log_tags p where p.tag_name = tag) then
	SET artwork_count = (SELECT p.artwork_count from pixiv_crawler_log_tags p where p.tag_name = tag limit 1);

-- 如果表中无数据，那么返回0
else
    SET artwork_count = 0;
    
end if;


END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `pixiv_crawler_tag_query` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `pixiv_crawler_tag_query`(
tag varchar(63),
OUT artwork_count mediumint
)
BEGIN

-- 如果表中有数据，那么返回该tag的作品数量
if exists (SELECT p.artwork_count from pixiv_crawler_log_tags p where p.tag_name = tag) then
	SET artwork_count = (SELECT p.artwork_count from pixiv_crawler_log_tags p where p.tag_name = tag limit 1);

-- 如果表中无数据，那么返回0
else
    SET artwork_count = 0;
    
end if;


END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `pixiv_crawler_tag_update` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `pixiv_crawler_tag_update`(
tag varchar(63),
count mediumint
)
BEGIN

-- 如果表中有数据，那么更新表数据
if exists (SELECT p.artwork_count from pixiv_crawler_log_tags p where p.tag_name = tag) then
    UPDATE pixiv_crawler_log_tags
		SET artwork_count = count,
			update_time = now()
        WHERE tag_name = tag;
-- 如果表中无数据，那么写入tag名称及其作品数量
else
    INSERT INTO pixiv_crawler_log_tags()
    VALUES(
    tag,
    count,
    now()
    );
end if;


END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `pixiv_crawler_update` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `pixiv_crawler_update`(
tag varchar(63),
count mediumint
)
BEGIN

-- 如果表中有数据，那么更新表数据
if exists (SELECT p.artwork_count from pixiv_crawler_log_tags p where p.tag_name = tag) then
    UPDATE pixiv_crawler_log_tags
		SET artwork_count = count,
			update_time = now()
        WHERE tag_name = tag;
-- 如果表中无数据，那么写入tag名称及其作品数量
else
    INSERT INTO pixiv_crawler_log_tags()
    VALUES(
    tag,
    count,
    now()
    );
end if;


END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-01-28  1:43:13
