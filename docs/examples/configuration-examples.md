# Configuration Examples

## Overview

This document provides practical configuration examples for the Pasture content scraping system. These examples range from basic setups to advanced configurations for different use cases.

## Basic Examples

### Minimal Configuration
```ini
# config.ini - Minimal setup
[worldnews]
url = https://www.reddit.com/r/worldnews.json

[hackernews_top]
type = hackernews
```

### Basic Multi-Source Setup
```ini
# config.ini - Basic multi-source configuration
[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
interval = 30

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = cryptocurrency, bitcoin
interval = 60

[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin, ethereum
interval = 60
```

## Advanced Examples

### Complete Multi-Source Configuration
```ini
# config.ini - Comprehensive multi-source setup

[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav

# Reddit Pastures
[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election, spam
remove_tags = header, aside
interval = 30

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = cryptocurrency, bitcoin, ethereum
interval = 60

[science]
url = https://www.reddit.com/r/science.json
blacklist = pseudoscience, conspiracy
interval = 120

# HackerNews Pastures
[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin, ethereum, spam
remove_tags = -nav
interval = 60

[hackernews_best]
type = hackernews
url = https://hacker-news.firebaseio.com/v0/beststories.json
blacklist = job, hiring, recruitment
interval = 120

# RSS Pastures
[tech_blog_rss]
type = rss
url = https://example.com/tech-feed.rss
blacklist = sponsored, advertisement
max_age_days = 7
interval = 240

[news_site_atom]
type = rss
url = https://example.com/news/atom.xml
blacklist = opinion, editorial
max_age_days = 3
interval = 180
```

### Domain-Specific Configuration
```ini
# config.ini - Domain-specific content aggregation

[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav, header, aside

# Technology News Aggregation
[arstechnica_reddit]
url = https://www.reddit.com/domain/arstechnica.com.json
blacklist = gaming, entertainment
interval = 60

[techcrunch_reddit]
url = https://www.reddit.com/domain/techcrunch.com.json
blacklist = funding, startup
interval = 60

[verge_reddit]
url = https://www.reddit.com/domain/theverge.com.json
blacklist = review, unboxing
interval = 60

# Programming & Development
[programming]
url = https://www.reddit.com/r/programming.json
blacklist = job, hiring, career
interval = 120

[python]
url = https://www.reddit.com/r/Python.json
blacklist = beginner, tutorial
interval = 180

[javascript]
url = https://www.reddit.com/r/javascript.json
blacklist = framework, library
interval = 180
```

## Use Case Examples

### News Aggregation
```ini
# config.ini - News aggregation setup

[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav, header, aside, form

# International News
[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election, opinion
interval = 30

[news]
url = https://www.reddit.com/r/news.json
blacklist = local, regional
interval = 30

# Technology News
[technology]
url = https://www.reddit.com/r/technology.json
blacklist = cryptocurrency, gaming
interval = 60

# Business News
[business]
url = https://www.reddit.com/r/business.json
blacklist = personal, finance
interval = 120

# HackerNews for Tech News
[hackernews_tech]
type = hackernews
blacklist = cryptocurrency, bitcoin, job, hiring
interval = 90

# RSS News Feeds
[reuters_rss]
type = rss
url = https://www.reutersagency.com/feed/?best-topics=tech&post_type=best
blacklist = sponsored, advertisement
max_age_days = 1
interval = 60

[ap_news_rss]
type = rss
url = https://www.apnews.com/apf-topnews
blacklist = sports, entertainment
max_age_days = 1
interval = 60
```

### Research & Academic Content
```ini
# config.ini - Academic and research content

[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav, header, aside

# Scientific Communities
[science]
url = https://www.reddit.com/r/science.json
blacklist = pseudoscience, conspiracy, opinion
interval = 120

[academia]
url = https://www.reddit.com/r/academia.json
blacklist = job, career, hiring
interval = 180

[math]
url = https://www.reddit.com/r/math.json
blacklist = homework, help
interval = 240

# Technology Research
[machinelearning]
url = https://www.reddit.com/r/MachineLearning.json
blacklist = job, career, beginner
interval = 120

[datascience]
url = https://www.reddit.com/r/datascience.json
blacklist = job, career, interview
interval = 180

# HackerNews for Research Papers
[hackernews_research]
type = hackernews
blacklist = cryptocurrency, bitcoin, startup, funding
interval = 120

# Academic RSS Feeds
[arxiv_cs_rss]
type = rss
url = http://arxiv.org/rss/cs
blacklist = 
max_age_days = 7
interval = 360

[nature_news_rss]
type = rss
url = https://www.nature.com/subjects/computer-science.rss
blacklist = advertisement, sponsored
max_age_days = 3
interval = 240
```

### Personal Interest Aggregation
```ini
# config.ini - Personal interests and hobbies

[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav

# Technology Interests
[programming]
url = https://www.reddit.com/r/programming.json
blacklist = job, hiring, career
interval = 120

[linux]
url = https://www.reddit.com/r/linux.json
blacklist = windows, macos
interval = 180

[selfhosted]
url = https://www.reddit.com/r/selfhosted.json
blacklist = commercial, proprietary
interval = 240

# Creative Interests
[photography]
url = https://www.reddit.com/r/photography.json
blacklist = gear, equipment, buying
interval = 180

[writing]
url = https://www.reddit.com/r/writing.json
blacklist = promotion, self-promotion
interval = 240

# Lifestyle Interests
[fitness]
url = https://www.reddit.com/r/fitness.json
blacklist = supplement, steroid
interval = 360

[cooking]
url = https://www.reddit.com/r/Cooking.json
blacklist = restaurant, review
interval = 360

# HackerNews for General Interest
[hackernews_personal]
type = hackernews
blacklist = cryptocurrency, bitcoin, job, hiring, politics
interval = 180

# Personal Blog RSS Feeds
[favorite_blog_rss]
type = rss
url = https://example.com/my-favorite-blog/feed/
blacklist = sponsored, advertisement
max_age_days = 14
interval = 480
```

## Environment-Specific Examples

### Development/Testing Configuration
```ini
# config.ini - Development and testing

[global]
remove_tags = script, style, noscript

# Test with small, fast subreddits
[test_small]
url = https://www.reddit.com/r/test.json
blacklist = 
interval = 5

# Test with different pasture types
[test_hackernews]
type = hackernews
blacklist = 
interval = 10

[test_rss]
type = rss
url = https://example.com/test-feed.rss
blacklist = 
max_age_days = 1
interval = 15
```

### Production Configuration
```ini
# config.ini - Production deployment

[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav, header, aside, form

# Conservative intervals for production
[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election, spam, offensive
interval = 120

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = cryptocurrency, bitcoin, spam
interval = 180

[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin, ethereum, spam
interval = 180

[tech_news_rss]
type = rss
url = https://example.com/tech-news.rss
blacklist = sponsored, advertisement
max_age_days = 2
interval = 240
```

## Specialized Configurations

### High-Volume Aggregation
```ini
# config.ini - High-volume content aggregation

[global]
remove_tags = script, style, noscript, iframe

# Frequent scraping for time-sensitive content
[breakingnews]
url = https://www.reddit.com/r/news.json
blacklist = local, regional
interval = 15

[worldnews_fast]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
interval = 20

# Multiple domain sources
[tech_domains]
url = https://www.reddit.com/domain/arstechnica.com+techcrunch.com+theverge.com.json
blacklist = gaming, entertainment
interval = 30

# HackerNews with frequent updates
[hackernews_frequent]
type = hackernews
url = https://hacker-news.firebaseio.com/v0/newstories.json
blacklist = job, hiring
interval = 30
```

### Niche Content Focus
```ini
# config.ini - Niche content focus

[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav

# AI & Machine Learning
[machinelearning]
url = https://www.reddit.com/r/MachineLearning.json
blacklist = job, career, beginner
interval = 120

[artificial]
url = https://www.reddit.com/r/artificial.json
blacklist = science fiction, movie
interval = 180

# Cybersecurity
[netsec]
url = https://www.reddit.com/r/netsec.json
blacklist = career, job
interval = 240

[cybersecurity]
url = https://www.reddit.com/r/cybersecurity.json
blacklist = career, job, beginner
interval = 240

# Specific Technology Stack
[reactjs]
url = https://www.reddit.com/r/reactjs.json
blacklist = job, career, hiring
interval = 360

[node]
url = https://www.reddit.com/r/node.json
blacklist = job, career, hiring
interval = 360

# Niche RSS Feeds
[ai_blog_rss]
type = rss
url = https://example.com/ai-research/feed/
blacklist = sponsored, advertisement
max_age_days = 14
interval = 480
```

## Configuration Tips

### Best Practices

1. **Start Simple**: Begin with minimal configuration and add complexity gradually
2. **Use Conservative Intervals**: Start with longer intervals (60+ minutes) and adjust based on needs
3. **Test Blacklists**: Verify blacklist terms work as expected before deploying to production
4. **Monitor Output**: Regularly check generated content to refine configuration
5. **Respect Rate Limits**: Be mindful of API rate limits and website terms of service

### Performance Optimization

- Use shorter intervals only for time-sensitive content
- Limit the number of active pastures to manage resource usage
- Use specific blacklist terms to reduce unnecessary processing
- Consider using domain-specific pastures instead of broad subreddits

### Error Prevention

- Always include `type` for non-Reddit pastures
- Ensure URLs are accessible and properly formatted
- Test configurations in development before deploying to production
- Monitor logs for configuration-related errors

These examples provide a solid foundation for configuring Pasture for various use cases. Adjust and combine these examples based on your specific needs and requirements.