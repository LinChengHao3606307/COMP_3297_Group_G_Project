
# COMP 3297 Group G Project

## Important docs:
- [vision doc](https://connecthkuhk-my.sharepoint.com/:w:/g/personal/u3606307_connect_hku_hk/IQD9kZZRnJiPTIxSGjKxoOG3Aex-NwIiyNTZywPfMKIx8PU?e=etTHGP)

- [use cases](https://connecthkuhk-my.sharepoint.com/:w:/g/personal/u3606307_connect_hku_hk/IQBa1r0PS0pQR6NRAKoLVzM7AddIPb8K779ircAi1OqJM6I?e=13hz48)

- [Product Backlog](https://connecthkuhk-my.sharepoint.com/:x:/g/personal/u3606307_connect_hku_hk/IQDszGtNJjNdQKKexfxhkStGATP01ZpfdjPUzL_VmQUFKXg?e=bDNYVA)

- [UI Storyboard](/COMP3297_Group_G.pdf)

- [Domain Model](#domain-model)


## Domain Model
```mermaid
classDiagram

    Course <|-- Advanced_Course
    Course <|-- General_Course

    Student <|-- CS_Student
    Student <|-- Non_CS_Student

    CS_Student "1..*" -- "0..*" Course : take
    Non_CS_Student "1..*" -- "0..*" General_Course : take
    Instructor "1" -- "0..*" Advanced_Course : teach
    Instructor "1" -- "0..*" Teaching_Team : join
    Student "1..*" -- "0..1" Teaching_Team : join
    Teaching_Team "1" -- "1" General_Course : teach
    
    class Course{
        int course_code
        String course_name
        int credit_value
        int enrolment_quota
    }
    class Advanced_Course{

    }
    class General_Course{

    }
    class Student{
        int uid
        String name
    }
    class CS_Student{
    }
    class Non_CS_Student{
    }
    class Instructor{
        int uid
        String name
    }
    class Teaching_Team{
    }
```
