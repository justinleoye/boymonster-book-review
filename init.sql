/*
Navicat MySQL Data Transfer

Source Server         : localhost
Source Server Version : 50128
Source Host           : localhost:3306
Source Database       : alex

Target Server Type    : MYSQL
Target Server Version : 50128
File Encoding         : 65001

Date: 2013-02-27 22:50:52
*/

SET FOREIGN_KEY_CHECKS=0;
-- ----------------------------
-- Table structure for `user`
-- ----------------------------

DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `userid` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `userpass` varchar(100) NOT NULL,
  `salt` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `tel` varchar(11) NOT NULL,
  PRIMARY KEY (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of user
-- ----------------------------

-- ----------------------------
-- Table structure for `user`
-- ----------------------------
DROP TABLE IF EXISTS `schoolmajor`;
CREATE TABLE `schoolmajor` (
  `schoolid` int(2) NOT NULL,
  `majorid` int(6) NOT NULL,
  PRIMARY KEY (`majorid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for `book`
-- ----------------------------
DROP TABLE IF EXISTS `book`;
CREATE TABLE `book` (
  `bookid` int(20) NOT NULL AUTO_INCREMENT,
  `doubanid` varchar(20) NOT NULL,
  `isbn` varchar(13) NOT NULL,
  PRIMARY KEY (`bookid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for `userbook`
-- ----------------------------
DROP TABLE IF EXISTS `userbook`;
CREATE TABLE `userbook` (
  `userbookid` int(24) NOT NULL AUTO_INCREMENT,
  `userid` int(11) NOT NULL,
  `isbn` varchar(13) NOT NULL,
  `major` varchar(6),
  `grade` varchar(1),
  `discount` int(1) NOT NULL,
  `extra` varchar(240),
  `date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`userbookid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for `orderlist`
-- ----------------------------
DROP TABLE IF EXISTS `orderlist`;
CREATE TABLE `orderlist` (
  `orderid` int(24) NOT NULL AUTO_INCREMENT,
  `userid` int(11) NOT NULL,
  `userbookid` int(24) NOT NULL,
  `date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`orderid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for `book_review`
-- ----------------------------
DROP TABLE IF EXISTS `book_review`;
CREATE TABLE `book_review` (
  `id` int(24) NOT NULL AUTO_INCREMENT,
  `isbn` varchar(13) NOT NULL,
  `userid` int(11) NOT NULL,
  `content` TEXT NOT NULL,
  `created` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

















