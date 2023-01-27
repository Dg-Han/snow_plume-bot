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
-- Table structure for table `fortune_greetings`
--

DROP TABLE IF EXISTS `fortune_greetings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fortune_greetings` (
  `greetings_fortune_id` int NOT NULL,
  `level_id` tinyint NOT NULL,
  `content` varchar(45) NOT NULL,
  PRIMARY KEY (`greetings_fortune_id`),
  UNIQUE KEY `greetings_fortune_id_UNIQUE` (`greetings_fortune_id`),
  KEY `fk_greetings_fortune_fortune_level1_idx` (`level_id`),
  CONSTRAINT `fk_greetings_fortune_fortune_level1` FOREIGN KEY (`level_id`) REFERENCES `fortune_levels` (`level_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fortune_greetings`
--

LOCK TABLES `fortune_greetings` WRITE;
/*!40000 ALTER TABLE `fortune_greetings` DISABLE KEYS */;
INSERT INTO `fortune_greetings` VALUES (1,1,'今天真的没有问题吗！！？'),(2,2,'轻雪酱会为你祈祷的！'),(3,3,'看来今天也会拥有小幸运呢！'),(4,4,'幸运的事会发生吧？'),(5,5,'今天会发生什么好事呢？'),(6,6,'现在的轻雪酱和你一样幸福！'),(7,6,'不管是想做的事情，还是想见的人，今天就是行动起来的好时机！'),(8,6,'今天是心想事成的一天喔！'),(9,5,'说不定会有意外之喜喔！'),(10,5,'和倒霉的同伴们分享一下好运气吧~'),(11,4,'是无论干什么都会很顺利的一天呢！'),(12,5,'风调雨顺，万事兴盛~'),(13,4,'无论是工作，还是生活，都一定会十分顺利吧！'),(14,6,'今天就是能挽回失去事物的好日子喔！'),(15,4,'地生万运，事事如意~'),(16,4,'今天是大展身手的好机会呢！'),(17,5,'明镜在心清如许，所求之事念则成~'),(18,5,'浮云散尽月当空，逢此签者为上吉~'),(19,4,'是舒畅又顺利的日子呢！'),(20,4,'大胆地拔剑，痛快地战斗一番吧！'),(21,4,'看来是令人舒心的一天~'),(22,3,'是一如既往的日常呢~'),(23,3,'稀松平常的日常，或许也是连续不断正发生的奇迹。'),(24,3,'是寻常的日子，也是宝贵的回忆。'),(25,3,'没有什么特别的事情，却也感到轻快愉悦的日子。'),(26,3,'路上的风景或许会让人眼前一亮~'),(27,3,'今天的食物或许会比平时更加鲜美~'),(28,4,'午睡时或许也能想到好点子~'),(29,3,'枯木逢春，万物复苏。陷入困境时，也会有解决办法吧！'),(30,3,'是会有一丝平淡怀念的日子呢，又稍微有一点点感伤。'),(31,2,'不用给自己过多压力，耐心等待彩虹吧！'),(32,2,'浮云遮月，迷雾漫漫呢！'),(33,2,'虽然一时迷惘，但也会有一切明了的时刻！'),(34,2,'不如趁此机会磨练自我，等待拨云见日吧！'),(35,3,'是平稳安详的一天呢。'),(36,2,'虽然有在原地打转的感觉...但也只是暂时的！'),(37,1,'在做出决定前，一定要再三思考喔！'),(38,1,'如果身体有不适，一定要注意休息喔！'),(39,1,'明明没什么大不了的事，却总感觉有些心烦呢。'),(40,1,'难免也会有这样的日子啊。'),(41,1,'虽然现在陷于低潮谷底中，但明天就会拨云见日，不必因此气馁喔！'),(42,1,'内心空落落的一天呢。'),(43,6,'今天有什么决定要做的吗？是千载难逢的好机会呢！'),(44,5,'会吃到格外好吃的东西呢！'),(45,5,'会看到格外漂亮的风景呢！');
/*!40000 ALTER TABLE `fortune_greetings` ENABLE KEYS */;
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
