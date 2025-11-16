# Documentation

This directory contains deployment guides and templates for Roane's Kitchen.

## Files

- **DEPLOYMENT.md** - Comprehensive Unraid deployment guide
- **unraid-template.xml** - Unraid Community Applications template (reference)
- **icon.png** - Application icon for Unraid CA (to be added)

## Creating an Icon

For Unraid Community Applications, create a 512x512 PNG icon:

1. Design icon (meal planning theme, kitchen utensils, calendar, etc.)
2. Save as `icon.png` (512x512, PNG format)
3. Commit to repository
4. Icon will be accessible at:
   `https://raw.githubusercontent.com/plongitudes/roanes-kitchen/main/docs/icon.png`

## Submitting to Unraid CA

Once ready for Community Applications:

1. Create icon.png in this directory
2. Test template XML validates
3. Fork https://github.com/Squidly271/AppFeed
4. Add template to appropriate category
5. Submit pull request

See: https://forums.unraid.net/topic/38582-docker-faq/

## Docker Compose Deployment

The recommended deployment method for Unraid is docker-compose via the Compose Manager plugin.

See DEPLOYMENT.md for full instructions.
