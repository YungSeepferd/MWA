"""
Enhanced CLI commands for MWA Core with notification testing capabilities.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Optional

import click
import httpx

from mwa_core.config import get_settings, Settings
from mwa_core.notifier import (
    NotificationManager,
    NotificationChannel,
    NotificationMessage,
    NotificationType,
    NotificationPriority,
    NotificationFormatter
)
from mwa_core.orchestrator import Orchestrator
from mwa_core.scraper import ScraperEngine
from mwa_core.storage import get_storage_manager

logger = logging.getLogger(__name__)


@click.group()
def cli():
    """MWA Core CLI commands."""
    pass


@cli.group()
def notify():
    """Notification system commands."""
    pass


@notify.command()
@click.option('--channel', '-c', multiple=True, help='Specific channels to test')
@click.option('--config', '-f', type=click.Path(exists=True), help='Configuration file path')
def test(channel: tuple, config: str):
    """Test notification configuration by sending test messages."""
    click.echo("Testing notification configuration...")
    
    try:
        # Load settings
        settings = get_settings() if not config else Settings.load(Path(config))
        
        # Create notification manager
        notification_manager = _create_notification_manager(settings)
        
        if not notification_manager.notifiers:
            click.echo("❌ No notifiers configured")
            return
        
        # Filter channels if specified
        test_channels = list(channel) if channel else None
        
        # Test each notifier
        results = {}
        for name, notifier in notification_manager.notifiers.items():
            channel_type = notifier.get_channel_type().value
            
            if test_channels and channel_type not in test_channels:
                continue
            
            click.echo(f"Testing {channel_type} notifier...")
            
            try:
                if hasattr(notifier, 'test_webhook'):
                    success = notifier.test_webhook()
                elif hasattr(notifier, 'test_connection'):
                    success = notifier.test_connection()
                else:
                    # Send a test notification
                    test_message = NotificationMessage(
                        type=NotificationType.SYSTEM_ALERT,
                        title="MWA Test Notification",
                        content="This is a test notification from MWA Core CLI.",
                        priority=NotificationPriority.NORMAL
                    )
                    
                    results_list = asyncio.run(notification_manager.send_notification(
                        test_message, 
                        channels=[notifier.get_channel_type()]
                    ))
                    success = any(r.is_successful for r in results_list)
                
                results[channel_type] = success
                status = "✅ PASS" if success else "❌ FAIL"
                click.echo(f"  {channel_type}: {status}")
                
            except Exception as e:
                results[channel_type] = False
                click.echo(f"  {channel_type}: ❌ FAIL - {e}")
        
        # Summary
        total = len(results)
        passed = sum(1 for r in results.values() if r)
        
        click.echo(f"\nTest Results: {passed}/{total} notifiers working")
        
        if passed == total:
            click.echo("🎉 All notifiers are working correctly!")
        else:
            click.echo("⚠️  Some notifiers failed. Check configuration and logs.")
            
    except Exception as e:
        click.echo(f"❌ Test failed: {e}")
        logger.error(f"Notification test failed: {e}")


@notify.command()
@click.option('--channel', '-c', default='discord', help='Channel to send test to')
@click.option('--title', '-t', default='Test Notification', help='Notification title')
@click.option('--message', '-m', default='This is a test notification from MWA Core.', help='Notification message')
@click.option('--priority', '-p', type=click.Choice(['low', 'normal', 'high', 'urgent']), default='normal', help='Notification priority')
@click.option('--config', '-f', type=click.Path(exists=True), help='Configuration file path')
def send(channel: str, title: str, message: str, priority: str, config: str):
    """Send a test notification."""
    click.echo(f"Sending test notification to {channel}...")
    
    try:
        # Load settings
        settings = get_settings() if not config else Settings.load(Path(config))
        
        # Create notification manager
        notification_manager = _create_notification_manager(settings)
        
        # Create test message
        test_message = NotificationMessage(
            type=NotificationType.SYSTEM_ALERT,
            title=title,
            content=message,
            priority=NotificationPriority(priority)
        )
        
        # Send notification
        results = asyncio.run(notification_manager.send_notification(
            test_message,
            channels=[NotificationChannel(channel)]
        ))
        
        # Report results
        successful = sum(1 for r in results if r.is_successful)
        total = len(results)
        
        click.echo(f"Notification sent: {successful}/{total} successful")
        
        for result in results:
            status = "✅" if result.is_successful else "❌"
            click.echo(f"  {result.channel.value}: {status}")
            if not result.is_successful and result.error_message:
                click.echo(f"    Error: {result.error_message}")
        
    except Exception as e:
        click.echo(f"❌ Failed to send notification: {e}")
        logger.error(f"Test notification failed: {e}")


@notify.command()
@click.option('--config', '-f', type=click.Path(exists=True), help='Configuration file path')
def stats(config: str):
    """Show notification delivery statistics."""
    try:
        # Load settings
        settings = get_settings() if not config else Settings.load(Path(config))
        
        # Create notification manager
        notification_manager = _create_notification_manager(settings)
        
        # Get stats
        stats = notification_manager.get_delivery_stats()
        
        click.echo("📊 Notification Statistics")
        click.echo("=" * 30)
        click.echo(f"Total sent: {stats['total_sent']}")
        click.echo(f"Successful: {stats['successful']}")
        click.echo(f"Failed: {stats['failed']}")
        click.echo(f"Success rate: {stats['success_rate']:.1%}")
        
        if stats['by_channel']:
            click.echo("\nBy Channel:")
            for channel, channel_stats in stats['by_channel'].items():
                click.echo(f"  {channel}: {channel_stats['successful']}/{channel_stats['total']} successful")
        
        if stats['recent_failures']:
            click.echo(f"\nRecent Failures ({len(stats['recent_failures'])}):")
            for failure in stats['recent_failures'][-5:]:  # Show last 5
                click.echo(f"  {failure['channel']}: {failure['error'][:50]}...")
        
    except Exception as e:
        click.echo(f"❌ Failed to get statistics: {e}")
        logger.error(f"Get stats failed: {e}")


@notify.command()
@click.option('--max-age', '-a', type=int, default=24, help='Maximum age in hours of failed notifications to retry')
@click.option('--config', '-f', type=click.Path(exists=True), help='Configuration file path')
def retry(max_age: int, config: str):
    """Retry failed notifications."""
    click.echo(f"Retrying failed notifications (max age: {max_age} hours)...")
    
    try:
        # Load settings
        settings = get_settings() if not config else Settings.load(Path(config))
        
        # Create notification manager
        notification_manager = _create_notification_manager(settings)
        
        # Retry failed notifications
        retried_count = asyncio.run(notification_manager.retry_failed_notifications(max_age))
        
        click.echo(f"✅ Retried {retried_count} failed notifications")
        
    except Exception as e:
        click.echo(f"❌ Retry failed: {e}")
        logger.error(f"Retry failed notifications failed: {e}")


@cli.group()
def orchestrator():
    """Orchestrator commands."""
    pass


@orchestrator.command()
@click.option('--providers', '-p', multiple=True, help='Specific providers to run')
@click.option('--config', '-f', type=click.Path(exists=True), help='Configuration file path')
@click.option('--dry-run', is_flag=True, help='Run without sending notifications')
@click.option('--test-notify', is_flag=True, help='Send test notification after run')
def run(providers: tuple, config: str, dry_run: bool, test_notify: bool):
    """Run the orchestrator with notification support."""
    click.echo("Starting orchestrator run...")
    
    try:
        # Load settings
        settings = get_settings() if not config else Settings.load(Path(config))
        
        # Determine providers to run
        enabled_providers = list(providers) if providers else settings.scraper.enabled_providers
        
        # Create components
        scraper = ScraperEngine()
        storage = get_storage_manager()
        
        # Create notification manager (unless dry run)
        notification_manager = None
        if not dry_run:
            notification_manager = _create_notification_manager(settings)
        
        # Create orchestrator
        orchestrator = Orchestrator(
            scraper=scraper,
            storage_manager=storage,
            notification_manager=notification_manager,
            settings=settings
        )
        
        # Run orchestrator
        click.echo(f"Running providers: {', '.join(enabled_providers)}")
        new_count = orchestrator.run(enabled_providers, settings.dict())
        
        click.echo(f"✅ Orchestrator completed. {new_count} new listings found.")
        
        # Send test notification if requested
        if test_notify and notification_manager:
            click.echo("Sending test notification...")
            test_message = NotificationMessage(
                type=NotificationType.SYSTEM_ALERT,
                title="MWA Orchestrator Test",
                content=f"Orchestrator run completed successfully. Found {new_count} new listings.",
                priority=NotificationPriority.NORMAL
            )
            
            results = asyncio.run(notification_manager.send_notification(test_message))
            successful = sum(1 for r in results if r.is_successful)
            click.echo(f"Test notification sent: {successful}/{len(results)} successful")
        
    except Exception as e:
        click.echo(f"❌ Orchestrator run failed: {e}")
        logger.error(f"Orchestrator run failed: {e}")


@orchestrator.command()
@click.option('--config', '-f', type=click.Path(exists=True), help='Configuration file path')
def test(config: str):
    """Test orchestrator notification configuration."""
    click.echo("Testing orchestrator notification configuration...")
    
    try:
        # Load settings
        settings = get_settings() if not config else Settings.load(Path(config))
        
        # Create orchestrator
        orchestrator = Orchestrator(settings=settings)
        
        # Test notifications
        results = orchestrator.test_notifications()
        
        if not results:
            click.echo("❌ No notifiers configured")
            return
        
        # Report results
        total = len(results)
        passed = sum(1 for r in results.values() if r)
        
        click.echo(f"Test Results: {passed}/{total} notifiers working")
        
        for channel, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            click.echo(f"  {channel}: {status}")
        
        if passed == total:
            click.echo("🎉 All notifiers are working correctly!")
        else:
            click.echo("⚠️  Some notifiers failed. Check configuration and logs.")
        
    except Exception as e:
        click.echo(f"❌ Test failed: {e}")
        logger.error(f"Orchestrator test failed: {e}")


@orchestrator.command()
@click.option('--config', '-f', type=click.Path(exists=True), help='Configuration file path')
def stats(config: str):
    """Show orchestrator notification statistics."""
    try:
        # Load settings
        settings = get_settings() if not config else Settings.load(Path(config))
        
        # Create orchestrator
        orchestrator = Orchestrator(settings=settings)
        
        # Get stats
        stats = orchestrator.get_notification_stats()
        
        if not stats.get('enabled'):
            click.echo("❌ Notifications are disabled")
            return
        
        click.echo("📊 Orchestrator Notification Statistics")
        click.echo("=" * 40)
        click.echo(f"Status: {'Enabled' if stats['enabled'] else 'Disabled'}")
        click.echo(f"Configured channels: {', '.join(stats['configured_channels'])}")
        click.echo(f"Total sent: {stats['total_sent']}")
        click.echo(f"Successful: {stats['successful']}")
        click.echo(f"Failed: {stats['failed']}")
        click.echo(f"Success rate: {stats['success_rate']:.1%}")
        
        if stats['by_channel']:
            click.echo("\nBy Channel:")
            for channel, channel_stats in stats['by_channel'].items():
                click.echo(f"  {channel}: {channel_stats['successful']}/{channel_stats['total']} successful")
        
    except Exception as e:
        click.echo(f"❌ Failed to get statistics: {e}")
        logger.error(f"Get orchestrator stats failed: {e}")


def _create_notification_manager(settings: Settings) -> NotificationManager:
    """Create notification manager from settings."""
    # Build notifier configuration
    notifier_config = {}
    
    # Add legacy notification config if available
    if settings.notification:
        notifier_config['notification'] = settings.notification.dict()
    
    # Add new notifier config if available
    if hasattr(settings, 'notifiers'):
        notifier_config['notifiers'] = settings.notifiers
    
    return NotificationManager(notifier_config)


if __name__ == '__main__':
    cli()