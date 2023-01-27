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
-- Table structure for table `pixiv_crawler_log_tags`
--

DROP TABLE IF EXISTS `pixiv_crawler_log_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pixiv_crawler_log_tags` (
  `tag_name` varchar(63) COLLATE utf8mb4_unicode_ci NOT NULL,
  `artwork_count` mediumint unsigned NOT NULL,
  `update_time` datetime NOT NULL,
  PRIMARY KEY (`tag_name`),
  UNIQUE KEY `tag_UNIQUE` (`tag_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pixiv_crawler_log_tags`
--

LOCK TABLES `pixiv_crawler_log_tags` WRITE;
/*!40000 ALTER TABLE `pixiv_crawler_log_tags` DISABLE KEYS */;
INSERT INTO `pixiv_crawler_log_tags` VALUES ('houteng',6,'2023-01-08 16:05:08'),('アークナイツ100000users入り',5,'2023-01-14 16:06:00'),('アークナイツ10000users入り',2194,'2023-01-14 15:52:09'),('アークナイツ1000users入り',16010,'2023-01-14 10:41:35'),('アークナイツ100users入り',7082,'2023-01-13 16:46:44'),('アークナイツ30000users入り',196,'2023-01-14 16:03:07'),('アークナイツ3000users入り',21,'2023-01-14 10:42:47'),('アークナイツ300users入り',4,'2023-01-13 16:46:56'),('アークナイツ50000users入り',44,'2023-01-14 16:05:39'),('アークナイツ5000users入り',3432,'2023-01-14 13:46:35'),('アークナイツ500users入り',2384,'2023-01-13 18:52:26'),('イレイナ',6404,'2023-01-18 15:15:47'),('キャル(プリコネ)',9731,'2023-01-12 13:09:12'),('キョウカ(プリコネ)',3283,'2023-01-11 17:06:45'),('コッコロ',11847,'2023-01-13 00:58:31'),('サトノダイヤモンド(ウマ娘)',5746,'2023-01-23 10:41:22'),('サレン(プリコネ)',2041,'2023-01-13 02:44:39'),('スマートファルコン(ウマ娘)',3287,'2023-01-22 15:36:01'),('バーチャルYouTuber100users入り',26812,'2023-01-27 00:34:46'),('バーチャルYouTuber300users入り',18,'2023-01-27 00:35:40'),('バーチャルYouTuber500users入り',11799,'2023-01-27 11:07:54'),('バニーガール',120891,'2023-01-22 10:44:09'),('ブルーアーカイブ100000users入り',5,'2023-01-17 15:37:00'),('ブルーアーカイブ10000users入り',1793,'2023-01-17 14:38:49'),('ブルーアーカイブ1000users入り',9314,'2023-01-17 10:35:15'),('ブルーアーカイブ100users入り',8092,'2023-01-16 22:23:44'),('ブルーアーカイブ30000users入り',70,'2023-01-17 15:34:12'),('ブルーアーカイブ3000users入り',2,'2023-01-17 10:35:25'),('ブルーアーカイブ300users入り',1,'2023-01-16 22:23:48'),('ブルーアーカイブ50000users入り',50,'2023-01-17 15:36:40'),('ブルーアーカイブ5000users入り',2718,'2023-01-17 13:01:28'),('ブルーアーカイブ500users入り',3158,'2023-01-17 01:21:00'),('ぼっち・ざ・ろっく!',18721,'2023-01-09 05:12:51'),('ぼっちちゃん',4881,'2023-01-08 15:48:38'),('ユニ(プリコネ)',3041,'2023-01-13 05:12:57'),('ユニコーン(アズールレーン)',6845,'2023-01-10 14:56:46'),('ライザリン・シュタウト',6192,'2023-01-11 14:27:58'),('ライスシャワー(ウマ娘)',19214,'2023-01-23 06:23:24'),('ラフィー(アズールレーン)',5609,'2023-01-10 11:25:58'),('ル・マラン(アズールレーン)',2861,'2023-01-10 20:54:40'),('伊地知虹夏',3098,'2023-01-08 03:29:31'),('原神100000users入り',93,'2023-01-16 12:25:24'),('原神10000users入り',6992,'2023-01-16 11:50:41'),('原神1000users入り',19560,'2023-01-15 22:36:21'),('原神100users入り',6798,'2023-01-15 00:35:50'),('原神30000users入り',2,'2023-01-16 11:50:50'),('原神3000users入り',112,'2023-01-15 22:42:31'),('原神300users入り',16,'2023-01-15 00:36:39'),('原神50000users入り',564,'2023-01-16 12:20:18'),('原神5000users入り',6574,'2023-01-16 04:35:54'),('原神500users入り',4779,'2023-01-15 04:43:37'),('喜多郁代',2899,'2023-01-08 12:16:51'),('山田リョウ(ぼっち・ざ・ろっく!)',1218,'2023-01-08 17:16:20'),('後藤ひとり',10656,'2023-01-08 10:21:56'),('後藤ふたり',242,'2023-01-22 13:01:54'),('愛宕(アズールレーン)',6808,'2023-01-19 06:17:51'),('極上の女体',43438,'2023-01-25 17:57:03'),('雪風(アズールレーン)',1308,'2023-01-10 00:05:22'),('鹿島(艦隊これくしょん)',9870,'2023-01-19 15:34:38');
/*!40000 ALTER TABLE `pixiv_crawler_log_tags` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-01-28  1:43:12
