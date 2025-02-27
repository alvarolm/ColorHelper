# ColorHelper 6.0.0

New release!

See `Preferences->Package Settings->ColorHelper->Changelog` for more info on  
prior releases.

A restart of Sublime Text is **strongly** encouraged.

Please report any issues as we _might_ have missed some required updates  
related to the upgrade to stable `coloraide`.

## 6.0.0

> **WARNING**: We finally made it to a stable `coloraide` 1.x.x release,  
> but some more unforeseen changes had to be made. This has been a long  
> road to get the underlying color library to a stable state.
>
> - User created custom plugins may need refactoring again, but most
>   should be unaffected.
> - If you tweaked the new`add_to_default_spaces`, please compare against
>   the default list as some plugins were renamed and user settings may
>   need to get updated. Color space plugins that do not properly load
>   should show log entries in the console.

- **NEW**: Upgraded to the stable `coloraide` 1.1. This should hopefully  
  eliminate API churn as it is now a stable release.
- **NEW**: Log when default color space loading fails.
