/**
 * Based on sample code provided by www.datastax.com, modified to use the homer/homestead
 * column family definitions and data structure.
 *
 * Original source: http://www.datastax.com/dev/blog/bulk-loading
 *                  http://www.datastax.com/wp-content/uploads/2011/08/DataImportExample.java
 */

/**
 * Disclaimer:
 * This file is an example on how to use the Cassandra SSTableSimpleUnsortedWriter class to create
 * sstables from a csv input file.
 * While this has been tested to work, this program is provided "as is" with no guarantee. Moreover,
 * it's primary aim is toward simplicity rather than completness. In partical, don't use this as an
 * example to parse csv files at home.
 */
import java.nio.ByteBuffer;
import java.io.*;
import java.util.UUID;

import org.apache.cassandra.db.marshal.*;
import org.apache.cassandra.io.sstable.SSTableSimpleUnsortedWriter;
import org.apache.cassandra.dht.Murmur3Partitioner;
import static org.apache.cassandra.utils.ByteBufferUtil.bytes;
import static org.apache.cassandra.utils.UUIDGen.decompose;

public class ClearwaterBulkProvisioner
{
    public static void main(String[] args) throws IOException
    {
        if (args.length != 2)
        {
            System.out.println("Usage:\n  BulkProvision <csv_file> <role>");
            System.exit(1);
        }

        String csvfile = args[0];
        String role = args[1];

        if (role.equals("homer")) {
            provision_homer(csvfile);
        } else if (role.equals("homestead-local")) {
            // Provision Homestead with cache and provisioning tables
            provision_homestead_cache(csvfile);
            provision_homestead_provisioning(csvfile);
        } else if (role.equals("homestead-hss")) {
            // Provision Homestead with cache tables only
            provision_homestead_cache(csvfile);
        } else {
           System.out.println("Only homer, homestead-local and homestead-hss roles are supported");
        }
    }

    private static void provision_homer(String csvfile) throws IOException
    {
        BufferedReader reader = new BufferedReader(new FileReader(csvfile));

        String keyspace = "homer";
        File ks_directory = new File(keyspace);
        if (!ks_directory.exists())
            ks_directory.mkdir();

        SSTableSimpleUnsortedWriter simservsWriter = createWriter(keyspace, "simservs");

        String line;
        int lineNumber = 1;
        CsvEntry entry = new CsvEntry();
        // There is no reason not to use the same timestamp for every column in that example.
        long timestamp = System.currentTimeMillis() * 1000;
        while ((line = reader.readLine()) != null)
        {
            if (entry.parse(line, lineNumber, csvfile))
            {
                simservsWriter.newRow(bytes(entry.public_id));
                simservsWriter.addColumn(bytes("value"), bytes(entry.simservs), timestamp);
            }
            lineNumber++;
        }
        // Don't forget to close!
        simservsWriter.close();
    }

    private static void provision_homestead_cache(String csvfile) throws IOException
    {
        BufferedReader reader = new BufferedReader(new FileReader(csvfile));

        /*
         * Create the directory to hold the cache keyspace.
         */
        String cache_keyspace = "homestead_cache";
        File cache_ks_directory = new File(cache_keyspace);
        if (!cache_ks_directory.exists())
            cache_ks_directory.mkdir();

        /*
         * Create SSTable writers for each table in the cache keyspace.
         */
        SSTableSimpleUnsortedWriter impiWriter = createWriter(cache_keyspace, "impi");
        SSTableSimpleUnsortedWriter impuWriter = createWriter(cache_keyspace, "impu");

        // There is no reason not to use the same timestamp for every column.
        long timestamp = System.currentTimeMillis() * 1000;

        /*
         * Walk through the supplied CSV, inserting rows in the keyspaces for each entry.
         */
        String line;
        int lineNumber = 1;
        CsvEntry entry = new CsvEntry();

        while ((line = reader.readLine()) != null)
        {
            if (entry.parse(line, lineNumber, csvfile))
            {
                impiWriter.newRow(bytes(entry.private_id));
                impiWriter.addColumn(bytes("_exists"), bytes(""), timestamp);
                impiWriter.addColumn(bytes("digest_ha1"), bytes(entry.digest), timestamp);
                impiWriter.addColumn(bytes("digest_realm"), bytes(entry.realm), timestamp);
                impiWriter.addColumn(bytes("public_id_" + entry.public_id), bytes(entry.public_id), timestamp);

                impuWriter.newRow(bytes(entry.public_id));
                impuWriter.addColumn(bytes("_exists"), bytes(""), timestamp);
                impuWriter.addColumn(bytes("ims_subscription_xml"), bytes(entry.imssubscription), timestamp);
            }
            lineNumber++;
        }

        // Don't forget to close!
        impiWriter.close();
        impuWriter.close();
    }

    private static void provision_homestead_provisioning(String csvfile) throws IOException
    {
        BufferedReader reader = new BufferedReader(new FileReader(csvfile));

        /*
         * Create the directory to hold the provisioning keyspace.
         */
        String prov_keyspace = "homestead_provisioning";
        File prov_ks_directory = new File(prov_keyspace);
        if (!prov_ks_directory.exists())
            prov_ks_directory.mkdir();

        /*
         * Create SSTable writers for each table in the provisioning keyspace.
         */
        SSTableSimpleUnsortedWriter irsWriter = createWriter(prov_keyspace, "implicit_registration_sets", UUIDType.instance);
        SSTableSimpleUnsortedWriter spWriter = createWriter(prov_keyspace, "service_profiles", UUIDType.instance);
        SSTableSimpleUnsortedWriter publicWriter = createWriter(prov_keyspace, "public");
        SSTableSimpleUnsortedWriter privateWriter = createWriter(prov_keyspace, "private");

        /*
         * Walk through the supplied CSV, inserting rows in the keyspaces for each entry.
         */
        String line;
        int lineNumber = 1;
        CsvEntry entry = new CsvEntry();

        // There is no reason not to use the same timestamp for every column.
        long timestamp = System.currentTimeMillis() * 1000;

        while ((line = reader.readLine()) != null)
        {
            if (entry.parse(line, lineNumber, csvfile))
            {
                irsWriter.newRow(entry.irs_uuid);
                irsWriter.addColumn(bytes("_exists"), bytes(""), timestamp);
                irsWriter.addColumn(bytes("associated_private_" + entry.private_id), bytes(entry.private_id), timestamp);
                irsWriter.addColumn(bytes("service_profile_" + entry.sp_uuid_str), entry.sp_uuid, timestamp);

                spWriter.newRow(entry.sp_uuid);
                spWriter.addColumn(bytes("_exists"), bytes(""), timestamp);
                spWriter.addColumn(bytes("public_identity_" + entry.public_id), bytes(entry.public_id), timestamp);
                spWriter.addColumn(bytes("initialfiltercriteria"), bytes(entry.ifc), timestamp);
                spWriter.addColumn(bytes("irs"), entry.irs_uuid, timestamp);

                publicWriter.newRow(bytes(entry.public_id));
                publicWriter.addColumn(bytes("_exists"), bytes(""), timestamp);
                publicWriter.addColumn(bytes("publicidentity"), bytes(entry.publicidentity_xml), timestamp);
                publicWriter.addColumn(bytes("service_profile"), entry.sp_uuid, timestamp);

                privateWriter.newRow(bytes(entry.private_id));
                privateWriter.addColumn(bytes("_exists"), bytes(""), timestamp);
                privateWriter.addColumn(bytes("digest_ha1"), bytes(entry.digest), timestamp);
                privateWriter.addColumn(bytes("realm"), bytes(entry.realm), timestamp);
                privateWriter.addColumn(bytes("associated_irs_" + entry.irs_uuid_str), entry.irs_uuid, timestamp);
            }
            lineNumber++;
        }

        // Don't forget to close!
        irsWriter.close();
        spWriter.close();
        publicWriter.close();
        privateWriter.close();
    }

    private static SSTableSimpleUnsortedWriter createWriter(String keyspace_name, String table_name) throws IOException
    {
        return createWriter(keyspace_name, table_name, AsciiType.instance);
    }

    private static SSTableSimpleUnsortedWriter createWriter(String keyspace_name, String table_name, AbstractType comparator) throws IOException
    {
        File directory = new File(keyspace_name + "/" + table_name);
        if (!directory.exists())
            directory.mkdir();

        return new SSTableSimpleUnsortedWriter(directory,
                                               new Murmur3Partitioner(),
                                               keyspace_name,
                                               table_name,
                                               comparator,
                                               null,
                                               64);
    }

    static class CsvEntry
    {
      String public_id, private_id, realm, digest, simservs, ifc, imssubscription, publicidentity_xml, irs_uuid_str, sp_uuid_str;
      ByteBuffer irs_uuid, sp_uuid;

        boolean parse(String line, int lineNumber, String csvfile)
        {
            // Ghetto csv parsing, will break if any entries contain commas.  This is fine at the moment because
            // neither the default simservs, nor the default IFC contain commas.
            String[] columns = line.split(",");
            if (columns.length != 10)
            {
                System.out.println(String.format("Invalid input '%s' at line %d of %s", line, lineNumber, csvfile));
                return false;
            }
            public_id = columns[0].trim();
            private_id = columns[1].trim();
            realm = columns[2].trim();
            digest = columns[3].trim();
            simservs = columns[4].trim();
            publicidentity_xml = columns[5].trim();
            ifc = columns[6].trim();
            imssubscription = columns[7].trim();
            irs_uuid_str = columns[8].trim();
            sp_uuid_str = columns[9].trim();

            // Convert the string representation of UUID to a byte array.  Apache Commons' UUID class has this
            // as built in function (as getRawBytes) but we don't have access to that class here, so we roll our
            // own.
            UUID uuid = UUID.fromString(irs_uuid_str);
            irs_uuid = ByteBuffer.wrap(decompose(uuid));
            UUID uuid2 = UUID.fromString(sp_uuid_str);
            sp_uuid = ByteBuffer.wrap(decompose(uuid2));

            return true;
        }
    }
}
