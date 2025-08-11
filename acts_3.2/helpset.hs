<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE helpset PUBLIC "-//Sun Microsystems Inc.//DTD JavaHelp HelpSet Version 2.0//EN" "http://java.sun.com/products/javahelp/helpset_2_0.dtd">
<helpset version="2.0">
    <title>ACTS Help</title>
     <maps>
          <mapref location="help_map.jhm"/>
          <homeID>ACTS.about</homeID>
     </maps>    
    <view mergetype="javax.help.AppendMerge">
        <name>TOC</name>
        <label>Table of Contents</label>
        <type>javax.help.TOCView</type>
        <data>help_toc.xml</data>
    </view>

    <view>
        <name>Search</name>
        <label>Text Utility Word Search</label>
        <type>javax.help.SearchView</type>
        <data engine="com.sun.java.help.search.DefaultSearchEngine">
        JavaHelpSearch
        </data>
     </view>
</helpset>
