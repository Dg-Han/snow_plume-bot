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
-- Table structure for table `fortune_charms`
--

DROP TABLE IF EXISTS `fortune_charms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fortune_charms` (
  `luck_charm_id` int NOT NULL,
  `item` varchar(20) NOT NULL,
  `content` varchar(45) NOT NULL,
  PRIMARY KEY (`luck_charm_id`),
  UNIQUE KEY `luck_charm_id_UNIQUE` (`luck_charm_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fortune_charms`
--

LOCK TABLES `fortune_charms` WRITE;
/*!40000 ALTER TABLE `fortune_charms` DISABLE KEYS */;
INSERT INTO `fortune_charms` VALUES (1,'带来幸运的「涩图」','据说多看涩图会变得更加幸运喔！'),(2,'炽热的「向日葵」','万事顺利是因为心中自有一条明路。'),(3,'鲜香的「麻婆豆腐」','麻辣爽滑的口感，据说和幸福的滋味很像。'),(4,'飞翔的「喜鹊」','带来春天的鸟儿，也在传递着幸运。'),(5,'羽状的「卷云」','如浪花般轻盈的云，带来新的思绪。'),(6,'无垠的「层云」','如被子般铺在世界上，予大地以温暖。'),(7,'厚实的「积云」','如泥土般厚重的云，筑牢内心的平稳。'),(8,'暗红的「赤豆」','不出众的外表里，也蕴含着丰富的营养。'),(9,'酸甜的「糖葫芦」','在童年的美食中，回味儿时的酸甜苦辣。'),(10,'烫手的「烘山芋」','传递到手心的温暖，存留在整个冬天。'),(11,'飘曳的「狗尾巴草」','于无止境的风涛中，也能游刃有余。'),(12,'挺拔的「杉松」','于刺骨的北风中，也能傲然挺立。'),(13,'茁壮成长的「白玉兰」','即使已然成熟，也仍维持着纯洁与真挚。'),(14,'艳丽的「火龙果」','在明艳的外貌下，隐藏着的是谦卑而甘甜的内在。'),(15,'水边的「垂柳」','柳叶飘扬，但在风停息时，柳树也如止水般安静。'),(16,'湖中的「月」','在夜空中散发光辉的明月，现在也变得触手可及。'),(17,'清晨的「云隙光」','偶尔能看见的景色，是日光许给这个世界的祝福。'),(18,'节节高升的「竹笋」','拥有无限潜力的竹笋，无人知晓它能够触达多高。'),(19,'散发暖意的「鸡蛋」','鸡蛋孕育着无限的可能性，是未来之种。'),(20,'掉落的「松果」','不是所有松果都能长成大树，成长需要适宜的环境，也需要一点运气。'),(21,'沉默的「仙人掌」','仙人掌在最恶劣的环境中也能存活，是相当强韧的生灵。'),(22,'生长的「绿萝」','只要有草木生长的空间，绿萝就可以绽放它的枝叶。'),(23,'随波摇曳的「海藻」','海藻是温柔而坚强的植物，即使在苦涩的海水中，也不会放弃柔软的心灵。'),(24,'来自远方的「蒲公英」','随风而起的种子，是你最好的象征。'),(25,'傲人的「牡丹」','生人勿近的高岭之花，也能让人的心情和头脑冷静下来。');
/*!40000 ALTER TABLE `fortune_charms` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-01-28  1:43:08
