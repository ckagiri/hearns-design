-- Core §5.6. Core writes the TTL as $ttl; here it is positional.
UPDATE tasks SET lease_expires_at = now() + $4::interval, last_heartbeat_at = now()
 WHERE id=$1 AND lease_holder=$2 AND attempts=$3 AND state='leased';
