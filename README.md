# COMP 3297 Group G Project
This project is aims at making BetaTrax, a software that links beta testers to developers and product owners.

## How to Use
Note: This is just a Minimum Viable Product. Detailed functionality (e.g. Permission checking, authentication) is not included.<br>



## Important docs:
- [vision doc](https://connecthkuhk-my.sharepoint.com/:w:/g/personal/u3606307_connect_hku_hk/IQD9kZZRnJiPTIxSGjKxoOG3Aex-NwIiyNTZywPfMKIx8PU?e=etTHGP)

- [use cases](https://connecthkuhk-my.sharepoint.com/:w:/g/personal/u3606307_connect_hku_hk/IQBa1r0PS0pQR6NRAKoLVzM7AddIPb8K779ircAi1OqJM6I?e=13hz48)

- [Product Backlog](https://connecthkuhk-my.sharepoint.com/:x:/g/personal/u3606307_connect_hku_hk/IQDszGtNJjNdQKKexfxhkStGATP01ZpfdjPUzL_VmQUFKXg?e=bDNYVA)

- [UI Storyboard](/COMP3297_Group_G.pdf)

- [Domain Model](#domain-model)


## Domain Model
```mermaid
classDiagram
    
    Product "1" -- "*" Report : belong_to
    Product "1" -- "1..*" Tester : test
    Product "1" -- "1" Product_Owner : own
    Product "1" -- "1..*" Developer : work_with

    Report "1" -- "1" Tester : written_by
    Report "*" -- "1" Product_Owner : reviewed_by
    Report "*" -- "0..1" Developer : claimed_by

    Product_Owner "1" -- "*" Report_Comment : write
    
    Developer "1..*" -- Product_Owner : work_under
    Developer "*" -- "*" Report_Comment : write

    Report_Comment "*" -- "1" Report : belong_to
    class Product{
        CharField_50 name
        IntegerField id
        CharField_20 version
    }
    class Report{
        IntegerField id
        CharField_20 status
        CharField_20 priority
        CharField_20 severity
        TextField assigned_to
        TextField title
        TextField description
        TextField steps_to_reproduce
        TextField tester_email
    }
    class Report_Comment{
        IntegerField id
        DateTimeField date
        TextField comment
    }
    class Tester{
        IntegerField id
    }
    class Product_Owner{
        IntegerField id
    }
    class Developer{
        IntegerField id
    }

```
