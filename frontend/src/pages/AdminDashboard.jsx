import { useEffect, useState } from 'react'
import { 
  Box, Flex, Heading, Text, Button, SimpleGrid, 
  Stat, StatLabel, StatNumber, StatHelpText, StatArrow,
  useColorModeValue, Spinner, Center, Table, Thead, Tbody, Tr, Th, Td,
  Badge, Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton, ModalFooter,
  FormControl, FormLabel, Select, Textarea, useDisclosure, Input, HStack, Icon,
  Tabs, TabList, TabPanels, Tab, TabPanel, Tag, Avatar, Image
} from '@chakra-ui/react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { servicios } from '../api/services'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

const STATUS_BADGES = {
  'PENDIENTE': 'red',
  'ASIGNADO': 'blue',
  'EN_PROCESO': 'orange',
  'RESUELTO': 'green',
  'CANCELADO': 'gray'
}

const PIPA_STATUS = {
  'DISPONIBLE': { color: 'green', label: 'Disponible' },
  'EN_RUTA': { color: 'blue', label: 'En Ruta' },
  'TALLER': { color: 'red', label: 'Mantenimiento' },
}

export default function AdminDashboard() {
  const [dashboardData, setDashboardData] = useState(null)
  const [grafica, setGrafica] = useState([])
  const [listaReportes, setListaReportes] = useState([]) 
  const [listaPipas, setListaPipas] = useState([])
  const [metricas, setMetricas] = useState({})

  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [selectedReporte, setSelectedReporte] = useState(null)
  const [formGestion, setFormGestion] = useState({
    status: '', nota_seguimiento: '', pipa_asignada: '', foto_solucion: null
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => { cargarTodo() }, [])

  const cargarTodo = async () => {
    try {
      const [resKpi, resGraf, resRep, resPipas] = await Promise.all([
        servicios.admin.getEstadisticas(),
        servicios.admin.getGraficaSemanal(),
        servicios.reportes.getAll(),
        servicios.pipas.getAll()
      ])
      setDashboardData(resKpi.data)
      setGrafica(resGraf.data)
      const repData = resRep.data
      setListaReportes(Array.isArray(repData) ? repData : (repData?.results ?? []))
      const pipaData = resPipas.data
      setListaPipas(Array.isArray(pipaData) ? pipaData : (pipaData?.results ?? []))
    } catch (error) {
      toast.error("Error cargando panel")
    } finally {
      setLoading(false)
    }

    // Métricas avanzadas — se cargan en segundo plano sin bloquear el panel
    try {
      const [resTasa, resTiempos, resZonas, resPipasEf, resRecurrentes] = await Promise.all([
        servicios.admin.getTasaResolucion(),
        servicios.admin.getTiempoResolucion(),
        servicios.admin.getZonasCalor(),
        servicios.admin.getEficienciaPipas(),
        servicios.admin.getReportesRecurrentes()
      ])
      setMetricas({
        tasa: resTasa.data,
        tiempos: resTiempos.data,
        zonas: resZonas.data,
        pipas: resPipasEf.data,
        recurrentes: resRecurrentes.data
      })
    } catch {
      // Métricas avanzadas no disponibles — no rompe el panel principal
    }
  }

  // --- HELPER PARA IMÁGENES ---
  const getImgUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    return `http://localhost:8000${url}`;
  }

  const handleGestionar = (reporte) => {
    setSelectedReporte(reporte)
    setFormGestion({
      status: reporte.status,
      nota_seguimiento: reporte.nota_seguimiento || '',
      pipa_asignada: reporte.pipa_asignada || '', 
      foto_solucion: null
    })
    onOpen()
  }

  const handleGuardarGestion = async () => {
    setSaving(true)
    const data = new FormData()
    data.append('status', formGestion.status)
    data.append('nota_seguimiento', formGestion.nota_seguimiento)
    if (formGestion.pipa_asignada) data.append('pipa_asignada', formGestion.pipa_asignada)
    if (formGestion.foto_solucion) data.append('foto_solucion', formGestion.foto_solucion)

    try {
      await servicios.reportes.gestionar(selectedReporte.id, data)
      toast.success(`Folio ${selectedReporte.folio} actualizado`)
      onClose()
      cargarTodo() 
    } catch (error) {
      toast.error("Error al actualizar")
    } finally {
      setSaving(false)
    }
  }

  if (loading || !dashboardData) {
    return (
      <Center h="100vh" bg="gray.100"><Spinner size="xl" color="blue.800" /><Text ml={4}>Cargando...</Text></Center>
    )
  }

  const stats = dashboardData.kpis

  return (
    <Box minH="100vh" bg="gray.50" p={8}>
      
      <Flex justify="space-between" align="center" mb={8} bg="white" p={4} borderRadius="lg" boxShadow="sm">
        <Box>
          <Heading size="lg" color="#691C32">Mesa de Control Operativa</Heading>
          <Text fontSize="sm" color="gray.500">Sistema de Aguas - Gobierno Municipal</Text>
        </Box>
        <Flex gap={4}>
          <Button colorScheme="gray" onClick={() => navigate('/inicio')}>Ir a Vista Ciudadana</Button>
          <Button as="a" href={servicios.admin.urlExportar} bg="#BC955C" color="white" _hover={{ bg: '#9c7b4a' }}>📥 Reporte Ejecutivo</Button>
        </Flex>
      </Flex>

      <SimpleGrid columns={{ base: 1, md: 4 }} spacing={5} mb={8}>
        <StatCard title="Total Expedientes" stat={stats.total_historico} icon="📂" />
        <StatCard title="Pendientes" stat={stats.pendientes_urgentes} icon="🚨" color="red.500" />
        <StatCard title="Concluidos" stat={stats.concluidos_exitosos} icon="✅" color="green.500" />
        <StatCard title="Falla Recurrente" stat={stats.falla_recurrente} icon="⚠️" />
      </SimpleGrid>

      <Tabs variant="enclosed" colorScheme="blue" bg="white" borderRadius="lg" boxShadow="sm">
        <TabList px={4} pt={4}>
            <Tab fontWeight="bold">🗺️ Mapa Táctico</Tab>
            <Tab fontWeight="bold">📋 Lista de Solicitudes</Tab>
            <Tab fontWeight="bold">🚚 Parque Vehicular</Tab>
            <Tab fontWeight="bold">📊 Estadísticas</Tab>
            <Tab fontWeight="bold">📈 Métricas Avanzadas</Tab>
        </TabList>

        <TabPanels>
            <TabPanel p={0} h="500px">
                <MapContainer center={[19.31, -98.88]} zoom={13} style={{ height: "100%", width: "100%" }}>
                    <TileLayer
                        attribution='Tiles &copy; Esri &mdash; Source: Esri'
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
                    />
                    {listaReportes.map((repo) => (
                        (repo.latitud && repo.longitud) && (
                            <Marker key={repo.id} position={[repo.latitud, repo.longitud]}>
                                <Popup>
                                    <Box minW="200px">
                                        <Badge colorScheme={STATUS_BADGES[repo.status]} mb={2}>{repo.status}</Badge>
                                        <Text fontWeight="bold" fontSize="sm">Folio: {repo.folio}</Text>
                                        <Text fontSize="xs">{repo.tipo_problema}</Text>
                                        {/* FOTO EVIDENCIA */}
                                        {repo.foto && (
                                            <Image 
                                                src={getImgUrl(repo.foto)} 
                                                alt="Evidencia" 
                                                borderRadius="md" 
                                                boxSize="120px" 
                                                objectFit="cover" 
                                                mt={2}
                                                fallbackSrc="https://via.placeholder.com/150?text=Sin+Imagen"
                                            />
                                        )}
                                        <Button size="xs" colorScheme="blue" w="full" mt={2} onClick={() => handleGestionar(repo)}>
                                            Gestionar / Asignar
                                        </Button>
                                    </Box>
                                </Popup>
                            </Marker>
                        )
                    ))}
                </MapContainer>
            </TabPanel>

            <TabPanel>
                <Box overflowX="auto">
                    <Table variant="simple" size="sm">
                        <Thead bg="gray.50"><Tr><Th>Folio</Th><Th>Tipo</Th><Th>Dirección</Th><Th>Estatus</Th><Th>Pipa</Th><Th>Acción</Th></Tr></Thead>
                        <Tbody>
                            {listaReportes.map(repo => (
                                <Tr key={repo.id}>
                                    <Td fontWeight="bold">{repo.folio}</Td>
                                    <Td>{repo.tipo_problema}</Td>
                                    <Td maxW="200px" isTruncated>{repo.direccion_texto}</Td>
                                    <Td><Badge colorScheme={STATUS_BADGES[repo.status]}>{repo.status}</Badge></Td>
                                    <Td>{repo.pipa_asignada ? <Tag size="sm" colorScheme="purple">🚛 Asignada</Tag> : '-'}</Td>
                                    <Td><Button size="xs" colorScheme="blue" onClick={() => handleGestionar(repo)}>Gestionar</Button></Td>
                                </Tr>
                            ))}
                        </Tbody>
                    </Table>
                </Box>
            </TabPanel>

            <TabPanel>
                <Table variant="striped" size="sm">
                    <Thead><Tr><Th>Unidad</Th><Th>Chofer</Th><Th>Estado</Th></Tr></Thead>
                    <Tbody>
                        {listaPipas.map(pipa => (
                            <Tr key={pipa.id}>
                                <Td fontWeight="bold">{pipa.numero_economico}</Td>
                                <Td>{pipa.chofer || 'Sin Chofer'}</Td>
                                <Td><Badge colorScheme={PIPA_STATUS[pipa.estado]?.color}>{pipa.estado}</Badge></Td>
                            </Tr>
                        ))}
                    </Tbody>
                </Table>
            </TabPanel>

            <TabPanel>
                <Box h="300px">
                    <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={grafica}><XAxis dataKey="fecha" /><YAxis /><Tooltip /><Bar dataKey="total" fill="#691C32" /></BarChart>
                    </ResponsiveContainer>
                </Box>
            </TabPanel>

            {/* ── MÉTRICAS AVANZADAS ─────────────────────────────────── */}
            <TabPanel>
              {/* 1. Tasa de Resolución */}
              <Box mb={8}>
                <Heading size="sm" mb={3} color="#691C32">Tasa de Resolución</Heading>
                <SimpleGrid columns={3} spacing={4} mb={4}>
                  <Box bg="gray.50" p={4} borderRadius="md" textAlign="center">
                    <Text fontSize="2xl" fontWeight="bold">{metricas.tasa?.global?.total ?? '—'}</Text>
                    <Text fontSize="sm" color="gray.500">Total expedientes</Text>
                  </Box>
                  <Box bg="green.50" p={4} borderRadius="md" textAlign="center">
                    <Text fontSize="2xl" fontWeight="bold" color="green.600">{metricas.tasa?.global?.resueltos ?? '—'}</Text>
                    <Text fontSize="sm" color="gray.500">Resueltos</Text>
                  </Box>
                  <Box bg="blue.50" p={4} borderRadius="md" textAlign="center">
                    <Text fontSize="2xl" fontWeight="bold" color="blue.600">{metricas.tasa?.global?.tasa_pct ?? '—'}%</Text>
                    <Text fontSize="sm" color="gray.500">Tasa global</Text>
                  </Box>
                </SimpleGrid>
                <Box overflowX="auto">
                  <Table variant="simple" size="sm">
                    <Thead bg="gray.50">
                      <Tr><Th>Tipo de Problema</Th><Th isNumeric>Total</Th><Th isNumeric>Resueltos</Th><Th isNumeric>Tasa</Th></Tr>
                    </Thead>
                    <Tbody>
                      {metricas.tasa?.por_tipo?.map((item, i) => (
                        <Tr key={i}>
                          <Td>{item.tipo_texto}</Td>
                          <Td isNumeric>{item.total}</Td>
                          <Td isNumeric>{item.resueltos}</Td>
                          <Td isNumeric>
                            <Badge colorScheme={item.tasa_pct >= 50 ? 'green' : 'orange'}>{item.tasa_pct}%</Badge>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              </Box>

              {/* 2. Tiempo Promedio de Resolución */}
              <Box mb={8}>
                <Heading size="sm" mb={3} color="#691C32">Tiempo Promedio de Resolución (horas)</Heading>
                {metricas.tiempos?.length > 0 ? (
                  <Box h="220px">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={metricas.tiempos}>
                        <XAxis dataKey="tipo_texto" tick={{ fontSize: 11 }} />
                        <YAxis unit="h" />
                        <Tooltip formatter={(v) => [`${v}h`, 'Promedio']} />
                        <Bar dataKey="promedio_horas" fill="#0B231E" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                ) : (
                  <Text color="gray.400" fontSize="sm">Sin reportes resueltos registrados aún.</Text>
                )}
              </Box>

              {/* 3. Zonas de Calor */}
              <Box mb={8}>
                <Heading size="sm" mb={3} color="#691C32">Colonias con Mayor Concentración de Reportes</Heading>
                <Box overflowX="auto">
                  <Table variant="simple" size="sm">
                    <Thead bg="gray.50">
                      <Tr><Th>Colonia</Th><Th isNumeric>Total</Th><Th isNumeric>Pendientes</Th><Th isNumeric>Resueltos</Th></Tr>
                    </Thead>
                    <Tbody>
                      {metricas.zonas?.por_colonia?.map((z, i) => (
                        <Tr key={i} bg={i < 3 ? 'red.50' : undefined}>
                          <Td fontWeight={i < 3 ? 'bold' : 'normal'}>{i < 3 ? '🔴 ' : ''}{z.colonia}</Td>
                          <Td isNumeric>{z.total}</Td>
                          <Td isNumeric><Badge colorScheme="red">{z.pendientes}</Badge></Td>
                          <Td isNumeric><Badge colorScheme="green">{z.resueltos}</Badge></Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              </Box>

              {/* 4. Eficiencia por Pipa */}
              <Box mb={8}>
                <Heading size="sm" mb={3} color="#691C32">Eficiencia por Unidad (Pipa)</Heading>
                <Box overflowX="auto">
                  <Table variant="simple" size="sm">
                    <Thead bg="gray.50">
                      <Tr><Th>Unidad</Th><Th>Chofer</Th><Th isNumeric>Servicios</Th><Th isNumeric>Completados</Th><Th isNumeric>Activos</Th><Th isNumeric>Eficiencia</Th></Tr>
                    </Thead>
                    <Tbody>
                      {metricas.pipas?.map((p, i) => (
                        <Tr key={i}>
                          <Td fontWeight="bold">{p.numero_economico}</Td>
                          <Td>{p.chofer || '—'}</Td>
                          <Td isNumeric>{p.servicios_totales}</Td>
                          <Td isNumeric>{p.servicios_resueltos}</Td>
                          <Td isNumeric>{p.servicios_activos}</Td>
                          <Td isNumeric>
                            <Badge colorScheme={p.eficiencia_pct >= 70 ? 'green' : p.eficiencia_pct >= 40 ? 'yellow' : 'gray'}>
                              {p.eficiencia_pct}%
                            </Badge>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              </Box>

              {/* 5. Reportes Recurrentes */}
              <Box>
                <Heading size="sm" mb={3} color="#691C32">Zonas con Problemas Recurrentes</Heading>
                <Box overflowX="auto">
                  <Table variant="simple" size="sm">
                    <Thead bg="gray.50">
                      <Tr><Th>Colonia</Th><Th>Tipo de Problema</Th><Th isNumeric>Recurrencias</Th><Th isNumeric>Sin Resolver</Th></Tr>
                    </Thead>
                    <Tbody>
                      {metricas.recurrentes?.length > 0 ? metricas.recurrentes.map((r, i) => (
                        <Tr key={i} bg={r.sin_resolver > 0 ? 'orange.50' : undefined}>
                          <Td>{r.colonia}</Td>
                          <Td>{r.tipo_texto}</Td>
                          <Td isNumeric><Badge colorScheme="purple">{r.cantidad}</Badge></Td>
                          <Td isNumeric>
                            <Badge colorScheme={r.sin_resolver > 0 ? 'red' : 'green'}>{r.sin_resolver}</Badge>
                          </Td>
                        </Tr>
                      )) : (
                        <Tr>
                          <Td colSpan={4} textAlign="center" color="gray.400" fontSize="sm">
                            Sin zonas recurrentes detectadas.
                          </Td>
                        </Tr>
                      )}
                    </Tbody>
                  </Table>
                </Box>
              </Box>
            </TabPanel>
        </TabPanels>
      </Tabs>

      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
            <ModalHeader>Gestión de Folio: {selectedReporte?.folio}</ModalHeader>
            <ModalCloseButton />
            <ModalBody py={6}>
                <SimpleGrid columns={2} spacing={4} mb={4}>
                    <Box><Text fontWeight="bold" fontSize="xs" color="gray.500">PROBLEMA</Text><Text>{selectedReporte?.tipo_problema}</Text></Box>
                    <Box><Text fontWeight="bold" fontSize="xs" color="gray.500">UBICACIÓN</Text><Text fontSize="sm">{selectedReporte?.direccion_texto}</Text></Box>
                    {/* VISUALIZAR FOTO EN EL MODAL DE GESTIÓN */}
                    {selectedReporte?.foto && (
                        <Box gridColumn="span 2">
                            <Text fontWeight="bold" fontSize="xs" color="gray.500" mb={1}>EVIDENCIA CIUDADANA</Text>
                            <Image src={getImgUrl(selectedReporte.foto)} borderRadius="md" maxH="200px" objectFit="contain" />
                        </Box>
                    )}
                </SimpleGrid>
                <FormControl mb={4}>
                    <FormLabel>Nuevo Estatus</FormLabel>
                    <Select value={formGestion.status} onChange={(e) => setFormGestion({...formGestion, status: e.target.value})}>
                        <option value="PENDIENTE">Pendiente</option>
                        <option value="ASIGNADO">Asignado a Cuadrilla</option>
                        <option value="EN_PROCESO">En Reparación</option>
                        <option value="RESUELTO">Resuelto</option>
                        <option value="CANCELADO">Improcedente</option>
                    </Select>
                </FormControl>
                <FormControl mb={4}>
                    <FormLabel>Asignar Pipa</FormLabel>
                    <Select placeholder="Sin asignación..." value={formGestion.pipa_asignada} onChange={(e) => setFormGestion({...formGestion, pipa_asignada: e.target.value})}>
                        {listaPipas.map(pipa => <option key={pipa.id} value={pipa.id}>{pipa.numero_economico} ({pipa.estado})</option>)}
                    </Select>
                </FormControl>
                <FormControl mb={4}>
                    <FormLabel>Nota de Seguimiento</FormLabel>
                    <Textarea value={formGestion.nota_seguimiento} onChange={(e) => setFormGestion({...formGestion, nota_seguimiento: e.target.value})} />
                </FormControl>
                <FormControl>
                    <FormLabel>Evidencia Solución (Foto)</FormLabel>
                    <Input type="file" p={1} onChange={(e) => setFormGestion({...formGestion, foto_solucion: e.target.files[0]})} />
                </FormControl>
            </ModalBody>
            <ModalFooter>
                <Button variant="ghost" mr={3} onClick={onClose}>Cancelar</Button>
                <Button colorScheme="blue" onClick={handleGuardarGestion} isLoading={saving}>Guardar</Button>
            </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

function StatCard({ title, stat, icon, color }) {
  return (
    <Box bg="white" p={5} borderRadius="lg" boxShadow="sm" borderLeft="4px solid" borderColor={color || 'gray.300'}>
      <Flex justify="space-between">
        <Box><Text fontSize="sm" color="gray.500" fontWeight="bold">{title}</Text><Heading size="lg" color="gray.700">{stat ?? '-'}</Heading></Box>
        <Text fontSize="3xl">{icon}</Text>
      </Flex>
    </Box>
  )
}