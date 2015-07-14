create table entity (
name     char(255) not null,
type     enum('file','subroutine','function','module','blockdata'),
fileid   integer not null,

index (name)
);

create table file (
fileid  integer not null auto_increment,
path    char(255) not null,
object  longblob not null,
date    timestamp not null,
status  enum('ok','error','warning') not null default 'ok',
version char(80),

primary key(fileid),
index(path)
);
