# PFP type inventory

AuthorityEffect: None.

The [strict domain models](../domain/type_register/type_register.py) validate
[type_register.yaml](type_register.yaml). The [file loader and census](../infrastructure/type_register.py)
use exact current package paths. No retired filename or documentation-directory
alias supplies a replacement model.

The combined application has 106 model/enum modules and 12 existing
public-name collisions. Rows remain marked for review. Equal class names do not
establish equal meanings, and this inventory is not a claim of schema unification.
