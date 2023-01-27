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
-- Table structure for table `fortune_get`
--

DROP TABLE IF EXISTS `fortune_get`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fortune_get` (
  `date` date NOT NULL,
  `user_id` char(12) NOT NULL,
  `fortune_value` tinyint NOT NULL,
  `level_id` tinyint NOT NULL,
  `greetings_fortune_id` int NOT NULL,
  `luck_charm_id` int NOT NULL,
  PRIMARY KEY (`date`,`user_id`),
  KEY `fk_get_fortune_users_idx` (`user_id`),
  KEY `fk_get_fortune_greetings_fortune1_idx` (`greetings_fortune_id`),
  KEY `fk_get_fortune_luck_charm1_idx` (`luck_charm_id`),
  KEY `fk_get_fortune_fortune_level1_idx` (`level_id`),
  CONSTRAINT `fk_get_fortune_fortune_level1` FOREIGN KEY (`level_id`) REFERENCES `fortune_levels` (`level_id`),
  CONSTRAINT `fk_get_fortune_greetings_fortune1` FOREIGN KEY (`greetings_fortune_id`) REFERENCES `fortune_greetings` (`greetings_fortune_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_get_fortune_luck_charm1` FOREIGN KEY (`luck_charm_id`) REFERENCES `fortune_charms` (`luck_charm_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_get_fortune_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fortune_get`
--

LOCK TABLES `fortune_get` WRITE;
/*!40000 ALTER TABLE `fortune_get` DISABLE KEYS */;
INSERT INTO `fortune_get` VALUES ('2022-12-10','1240207978',23,3,3,1),('2022-12-10','1500723170',18,3,3,1),('2022-12-11','1240207978',91,5,17,6),('2022-12-15','1240207978',63,4,13,19),('2022-12-16','1240207978',9,2,33,23),('2023-01-12','1240207978',3,2,33,17);
/*!40000 ALTER TABLE `fortune_get` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-01-28  1:43:09
