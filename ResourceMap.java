import java.io.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

final class ResourceMap {
    private static final String REDIRECT_DEFS_FILENAME = "/redirect.defs";

    private ResourceMap() {}

    public static Map<String, byte[]> loadFiles() throws IOException {
        Map<String, byte[]> resources = new HashMap<String, byte[]>();

        final String dir = System.getProperty("user.dir") + "/www";
        System.out.println("web root = " + dir);
        List<File> files = getFilesInDir(new File(dir));
        for (File file : files) {
            String relativeWebPath = file.getPath().replaceFirst(dir, "");
            if (!relativeWebPath.equals(REDIRECT_DEFS_FILENAME)) {
                System.out.println(relativeWebPath);
                resources.put(relativeWebPath, read(file));
            }
        }
        return resources;
    }

    public static Map<String, String> loadRedirects() throws IOException {
        Map<String, String> redirect = new HashMap<String, String>();

        final String dir = System.getProperty("user.dir") + "/www";
        System.out.println("web root = " + dir);
        File redirFile = new File(dir + REDIRECT_DEFS_FILENAME);
        if (!redirFile.exists()) {
            System.out.println("No redirects defined (file does not exist).");
        } else {
            String contents = new String(read(redirFile));
            for (String line : contents.split("\n")) {
                System.out.println(line);
                String[] parts = line.split(" ");
                if (parts.length == 2) {
                    redirect.put(parts[0], parts[1]);
                }
            }
        }
        return redirect;
    }

    public static String contentTypeFromFilename(String fileName) {
        if (fileName.endsWith(".html") || fileName.endsWith(".htm")) {
            return "text/html";
        } else if (fileName.endsWith(".jpg") || fileName.endsWith(".jpeg")) {
            return "image/jpg";
        } else if (fileName.endsWith(".png")) {
            return "image/png";
        } else if (fileName.endsWith(".gif")) {
            return "image/png";
        } else if (fileName.endsWith(".css")) {
            return "text/css";
        } else if (fileName.endsWith(".txt")) {
            return "text/plain";
        } else if (fileName.endsWith(".pdf")) {
            return "application/pdf";
        } else if (fileName.endsWith(".bz2")) {
            return "application/bzip2";
        } else {
            return "application/octet-stream";
        }
    }

    private static List<File> getFilesInDir(File directory) {
        List<File> files = new ArrayList<File>();
        for (File file : directory.listFiles()) {
            if (file.isDirectory()) {
                files.addAll(getFilesInDir(file));
            } else if (file.isFile()) {
                files.add(file);
            }
        }
        return files;
    }

    /** Read the given binary file, and return its contents as a byte array.*/
    private static byte[] read(File inFile) throws IOException {
        InputStream in = new BufferedInputStream(new FileInputStream(inFile));
        int fileBytes = (int) inFile.length();
        byte[] inByteBuf = new byte[fileBytes];

        for (int totalBytesRead = 0; totalBytesRead < fileBytes; ) {
            int bytesRead = in.read(inByteBuf, totalBytesRead, fileBytes-totalBytesRead);
            if (bytesRead < 0) {
                System.out.println(String.format("bytesRead = %d", bytesRead));
            } else {
                totalBytesRead += bytesRead;
            }
        }
        return inByteBuf;
    }
}
